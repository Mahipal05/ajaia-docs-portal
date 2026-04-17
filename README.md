# DocSprint

DocSprint is a lightweight collaborative document editor built for the Ajaia AI-Native Full Stack Developer assignment. It focuses on the strongest end-to-end slice for the timebox: document creation, rich-text editing, file import, sharing, persistence, and review-ready documentation.

## What works

- Create a new document from the dashboard
- Rename and edit document content in the browser
- Apply bold, italic, underline, headings, bullet lists, and numbered lists
- Save and reopen documents with HTML formatting preserved in SQLite
- Import `.txt`, `.md`, and `.html` files as new editable documents
- Share a document from its owner to another seeded demo user
- View owned and shared documents in separate dashboard sections
- Edit shared documents as a non-owner after access is granted
- Run automated tests for the core create, save, import, and share flows

## Stack

- Backend: Flask
- Persistence: SQLite with the Python standard library
- Frontend: Server-rendered Jinja templates plus small vanilla JavaScript for the editor
- Styling: Custom CSS, no external UI framework

## Demo users

No password is required. Reviewers can switch between seeded users directly in the UI.

- Mahipal Baithi: `mahipal.baithi05@gmail.com`
- Ava Sharma: `ava@ajaia.local`
- Noah Patel: `noah@ajaia.local`

## Supported imports

- `.txt`
- `.md`
- `.html`

The app intentionally does not support `.docx` in this version. That scope cut is explicit in the UI and here in the README.

## Local setup

### 1. Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Run the app

```powershell
python app/__init__.py
```

Then open [http://127.0.0.1:5000](http://127.0.0.1:5000).

By default the SQLite database is stored in the system temp folder (`%TEMP%\docsprint\portal.db` on Windows). You can override that location with the `DOCSPRINT_DATABASE` environment variable if you want a more permanent local path or a production deployment path.

## Run tests

```powershell
python -m unittest discover -s tests
```

## Project structure

```text
ajaia-docs-portal/
  app/
    static/
    templates/
    __init__.py
    database.py
    importers.py
  tests/
  AI_WORKFLOW.md
  ARCHITECTURE.md
  Dockerfile
  README.md
  SUBMISSION.md
  main.py
  walkthrough-video-url.txt
```

## Deployment notes

### Render

The repo now includes [render.yaml](C:\Users\ASUS\OneDrive\Documents\Playground\ajaia-docs-portal\render.yaml) for a straightforward Render deployment and [RENDER_DEPLOY.md](C:\Users\ASUS\OneDrive\Documents\Playground\ajaia-docs-portal\RENDER_DEPLOY.md) for the exact steps.

Quick path:

1. Push this folder to GitHub as its own repo if possible.
2. In Render, create a new web service from that repo.
3. Let Render use the included `render.yaml`, or configure manually with:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn wsgi:app`
   - Health Check Path: `/health`
4. Use the deployed `onrender.com` URL in `SUBMISSION.md`.

Important:

- Render web services must listen on `0.0.0.0` and a platform port; the app already supports that.
- Render's filesystem is ephemeral by default. If you want SQLite data to survive deploys and restarts, attach a persistent disk and mount it at `/opt/render/project/src/render-data`.
- Without a persistent disk, SQLite still works for demo and refresh-level persistence during a running instance, but not across service restarts.

### Docker

This repository also includes a `Dockerfile` if you prefer deploying through Docker on another platform.

## Known limitations

- The editor uses `document.execCommand`, which is deprecated but still practical for a fast, dependency-light take-home build.
- HTML is stored as the document source of truth. That keeps formatting intact but is not hardened for untrusted multi-tenant input.
- Sharing is a simple access grant model without granular roles, revocation, or audit history.
- SQLite is perfect for the assignment scope, but a deployed multi-user version should move to a managed database plus stronger auth.
- On Render, durable SQLite storage across deploys and restarts requires a persistent disk because the default filesystem is ephemeral.
