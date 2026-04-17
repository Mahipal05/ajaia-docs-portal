# Walkthrough Video Script

Target length: 3.5 to 4.5 minutes

## 0:00 - 0:30

Introduce the app:

> This is DocSprint, a lightweight collaborative document editor I built for the Ajaia take-home assignment. I scoped it around the strongest core slice: document creation, rich-text editing, file import, simple sharing, persistence, and review-ready deployment/documentation.

## 0:30 - 1:20

Show the dashboard:

- Mention the seeded users and lightweight login choice
- Point out the owned vs shared document sections
- Show the create-document card
- Show the file-import card and supported formats: `.txt`, `.md`, `.html`

Suggested line:

> I intentionally used seeded demo users instead of full auth so the reviewer can verify sharing quickly without setup friction.

## 1:20 - 2:20

Create and edit a document:

- Create a blank document
- Rename it
- Add content
- Demonstrate bold, italic, underline
- Demonstrate headings and one list
- Save changes

Suggested line:

> The editor is built as a focused rich-text surface with a formatting toolbar. It is not trying to replicate Google Docs fully, but it does provide a coherent editing flow for the assignment scope.

## 2:20 - 3:00

Show file import:

- Go back to dashboard
- Import a markdown file
- Open the imported result
- Point out that the content becomes editable HTML in the editor

Suggested line:

> For file upload, I chose product-relevant document import. Uploaded `.txt`, `.md`, and `.html` files become new editable documents.

## 3:00 - 3:45

Show sharing:

- Open an owned document
- Share it with Ava or Noah
- Switch users
- Open the shared document from the shared section

Suggested line:

> The sharing model includes a document owner, grant-based access, and a visible distinction between owned and shared docs. Shared users can edit, but only the owner can grant new access.

## 3:45 - 4:20

Close with architecture and AI usage:

- Mention Flask + SQLite + server-rendered UI
- Mention automated tests
- Mention deployment on Render
- Mention AI usage briefly and honestly

Suggested line:

> I used AI to speed up scaffolding, UI drafting, and documentation, but I manually made the scope cuts, data model decisions, validation paths, and final UX tradeoffs. I also added automated tests around the highest-value flows.

## 4:20 - 4:40

State what you deprioritized:

- `.docx` import
- real auth
- real-time collaboration
- granular permissions
- version history

Suggested closing:

> With another few hours, I’d replace the lightweight editor implementation with a richer editor framework, add role-based sharing, and move production persistence to a managed database or a persistent disk-backed setup.
