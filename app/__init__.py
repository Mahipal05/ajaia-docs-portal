from __future__ import annotations

import os
import tempfile
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

try:
    from . import database
    from .importers import SUPPORTED_EXTENSIONS, UnsupportedImportError, html_preview, import_file
except ImportError:  # Support `python app/__init__.py` from the repo root.
    import database
    from importers import SUPPORTED_EXTENSIONS, UnsupportedImportError, html_preview, import_file


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    local_root = Path(tempfile.gettempdir()) / "docsprint"
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "ajaia-docs-portal-dev"),
        DATABASE=os.environ.get("DOCSPRINT_DATABASE", os.path.join(local_root, "portal.db")),
        MAX_CONTENT_LENGTH=2 * 1024 * 1024,
    )

    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    database.init_database(app.config["DATABASE"])

    @app.before_request
    def load_current_user():
        user_id = session.get("user_id")
        g.current_user = database.get_user(app.config["DATABASE"], user_id) if user_id else None

    @app.context_processor
    def inject_globals():
        return {
            "current_user": g.get("current_user"),
            "supported_extensions": ", ".join(sorted(SUPPORTED_EXTENSIONS)),
        }

    @app.template_filter("datetime_label")
    def datetime_label(value: str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value
        return dt.strftime("%b %d, %Y at %I:%M %p")

    def login_required(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            if g.current_user is None:
                return redirect(url_for("login", next=request.path))
            return view(*args, **kwargs)
        return wrapped_view

    def current_user_id():
        if g.current_user is None:
            abort(401)
        return int(g.current_user["id"])

    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

    @app.route("/login", methods=["GET", "POST"])
    def login():
        users = database.fetch_users(app.config["DATABASE"])
        if request.method == "POST":
            user_id = request.form.get("user_id", type=int)
            user = database.get_user(app.config["DATABASE"], user_id) if user_id else None
            if user is None:
                flash("Please choose a valid demo user.", "error")
            else:
                session.clear()
                session["user_id"] = int(user["id"])
                destination = request.args.get("next") or url_for("dashboard")
                return redirect(destination)
        return render_template("login.html", users=users)

    @app.post("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.get("/")
    @login_required
    def dashboard():
        owned_docs, shared_docs = database.get_dashboard_documents(
            app.config["DATABASE"], current_user_id()
        )
        owned_cards = [
            {
                **dict(row),
                "preview": html_preview(row["content_html"]),
            }
            for row in owned_docs
        ]
        shared_cards = [
            {
                **dict(row),
                "preview": html_preview(row["content_html"]),
            }
            for row in shared_docs
        ]
        return render_template(
            "dashboard.html",
            owned_documents=owned_cards,
            shared_documents=shared_cards,
            demo_users=database.fetch_users(app.config["DATABASE"]),
        )

    @app.post("/documents")
    @login_required
    def create_document():
        title = (request.form.get("title") or "").strip() or "Untitled document"
        title = title[:120]
        doc_id = database.create_document(
            app.config["DATABASE"], current_user_id(), title=title
        )
        flash("Document created. Start typing when you're ready.", "success")
        return redirect(url_for("document_editor", document_id=doc_id))

    @app.post("/documents/import")
    @login_required
    def import_document():
        uploaded_file = request.files.get("import_file")
        custom_title = (request.form.get("title") or "").strip()

        if uploaded_file is None or not uploaded_file.filename:
            flash("Choose a file to import.", "error")
            return redirect(url_for("dashboard"))

        try:
            imported = import_file(uploaded_file.filename, uploaded_file.read())
        except UnsupportedImportError as exc:
            flash(str(exc), "error")
            return redirect(url_for("dashboard"))

        title = (custom_title or imported.suggested_title)[:120]
        doc_id = database.create_document(
            app.config["DATABASE"],
            current_user_id(),
            title=title,
            content_html=imported.content_html,
            source_filename=uploaded_file.filename,
        )
        flash(f"Imported {uploaded_file.filename} into a new document.", "success")
        return redirect(url_for("document_editor", document_id=doc_id))

    @app.get("/documents/<int:document_id>")
    @login_required
    def document_editor(document_id):
        doc = database.get_document(
            app.config["DATABASE"], document_id, viewer_id=current_user_id()
        )
        if not doc:
            abort(404)

        is_owner = int(doc["owner_id"]) == current_user_id()
        shared_users = database.get_shared_users(app.config["DATABASE"], document_id)
        share_candidates = (
            database.get_share_candidates(app.config["DATABASE"], document_id, current_user_id())
            if is_owner
            else []
        )

        return render_template(
            "editor.html",
            document=doc,
            is_owner=is_owner,
            shared_users=shared_users,
            share_candidates=share_candidates,
        )

    @app.post("/documents/<int:document_id>/share")
    @login_required
    def share_document(document_id):
        doc = database.get_document(
            app.config["DATABASE"], document_id, viewer_id=current_user_id()
        )
        if not doc:
            abort(404)
        if int(doc["owner_id"]) != current_user_id():
            abort(403)

        target_user_id = request.form.get("target_user_id", type=int)
        if not target_user_id:
            flash("Pick a teammate to share with.", "error")
            return redirect(url_for("document_editor", document_id=document_id))

        if database.add_share(
            app.config["DATABASE"], document_id, current_user_id(), target_user_id
        ):
            flash("Access granted.", "success")
        else:
            flash("Unable to share this document with that user.", "error")
        return redirect(url_for("document_editor", document_id=document_id))

    @app.post("/api/documents/<int:document_id>/save")
    @login_required
    def save_document(document_id):
        data = request.get_json(silent=True) or {}
        title = (data.get("title") or "").strip()
        content_html = (data.get("content_html") or "").strip()

        if not title:
            return jsonify({"error": "Title is required."}), 400
        if len(title) > 120:
            return jsonify({"error": "Title must be 120 characters or fewer."}), 400
        if len(content_html) > 200_000:
            return jsonify({"error": "Document content is too large."}), 400

        updated = database.update_document(
            app.config["DATABASE"],
            document_id=document_id,
            user_id=current_user_id(),
            title=title,
            content_html=content_html,
        )
        if not updated:
            return jsonify({"error": "Document not found or access denied."}), 404
        return (
            jsonify(
                {
                    "id": int(updated["id"]),
                    "title": updated["title"],
                    "updated_at": updated["updated_at"],
                }
            ),
            200,
        )

    @app.errorhandler(403)
    def forbidden(_error):
        return (
            render_template(
                "error.html",
                title="Access denied",
                message="You do not have permission to view that document.",
            ),
            403,
        )

    @app.errorhandler(404)
    def not_found(_error):
        return (
            render_template(
                "error.html",
                title="Not found",
                message="The page you requested does not exist or is not shared with you.",
            ),
            404,
        )

    @app.errorhandler(413)
    def too_large(_error):
        flash("File too large. Please keep uploads under 2 MB.", "error")
        return redirect(url_for("dashboard"))

    return app


# ✅ THIS PART FIXES RENDER DEPLOYMENT
def run_dev_server() -> None:
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG") == "1"
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=debug)


if __name__ == "__main__":
    run_dev_server()
