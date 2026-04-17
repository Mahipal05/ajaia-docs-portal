# Render Deploy Guide

This is the fastest path to getting a live URL for the assignment.

## Recommended repo shape

Push `ajaia-docs-portal` as its own GitHub repository if possible. That makes deployment cleaner because the included `render.yaml` will sit at the repo root.

If you keep this inside a larger repo, set Render's **Root Directory** to `ajaia-docs-portal`.

## Deployment steps

1. Push the code to GitHub.
2. In Render, click **New > Web Service**.
3. Connect the repository.
4. If Render asks whether to use the Blueprint, allow it to use `render.yaml`.
5. If you are configuring manually, use:
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn wsgi:app`
   - Health Check Path: `/health`
6. Add or confirm these environment variables:
   - `PYTHON_VERSION=3.11.11`
   - `DOCSPRINT_DATABASE=/opt/render/project/src/render-data/portal.db`
7. Deploy and wait for the `onrender.com` URL.

## Persistence note

Render's filesystem is ephemeral by default, which means local file changes are lost on redeploy or restart. If you want the SQLite database to persist across deploys and restarts, attach a persistent disk on a paid web service and mount it at:

`/opt/render/project/src/render-data`

That matches the configured `DOCSPRINT_DATABASE` path.

## Post-deploy smoke test

After the service is live:

1. Open the login page.
2. Create a document as Mahipal.
3. Save formatted content.
4. Share it with Ava.
5. Switch users and confirm the shared document appears.
6. Copy the public URL into `SUBMISSION.md`.

## Useful links

- [Deploy a Flask app on Render](https://render.com/docs/deploy-flask)
- [Render web services](https://render.com/docs/web-services)
- [Persistent disks on Render](https://render.com/docs/disks)
- [Blueprint YAML reference](https://render.com/docs/blueprint-spec)
