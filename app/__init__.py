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

from . import database
from .importers import SUPPORTED_EXTENSIONS, UnsupportedImportError, html_preview, import_file


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
                return redirect(url_for("dashboard"))
        return render_template("login.html", users=users)

    @app.get("/")
    @login_required
    def dashboard():
        owned_docs, shared_docs = database.get_dashboard_documents(
            app.config["DATABASE"], current_user_id()
        )
        return render_template(
            "dashboard.html",
            owned_documents=owned_docs,
            shared_documents=shared_docs,
            demo_users=database.fetch_users(app.config["DATABASE"]),
        )

    @app.post("/documents")
    @login_required
    def create_document():
        title = (request.form.get("title") or "Untitled document")[:120]
        doc_id = database.create_document(
            app.config["DATABASE"], current_user_id(), title=title
        )
        return redirect(url_for("document_editor", document_id=doc_id))

    @app.get("/documents/<int:document_id>")
    @login_required
    def document_editor(document_id):
        doc = database.get_document(
            app.config["DATABASE"], document_id, viewer_id=current_user_id()
        )
        if not doc:
            abort(404)
        return render_template("editor.html", document=doc)

    @app.post("/api/documents/<int:document_id>/save")
    @login_required
    def save_document(document_id):
        data = request.get_json()
        updated = database.update_document(
            app.config["DATABASE"],
            document_id,
            current_user_id(),
            data["title"],
            data["content_html"],
        )
        if not updated:
            return {"error": "Not found"}, 404
        return {"status": "saved"}

    return app


# ✅ THIS PART FIXES RENDER DEPLOYMENT
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=10000)