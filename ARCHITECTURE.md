# Architecture Note

## Goal

Ship the strongest realistic product slice within a 4-6 hour take-home window, not a maximal Google Docs clone.

## What I prioritized

### 1. End-to-end product completeness over framework complexity

I chose Flask plus server-rendered templates instead of a SPA stack so I could spend time on the actual assignment surfaces:

- document creation
- rich-text editing
- file import
- sharing
- persistence
- usability polish
- tests and reviewer docs

That tradeoff reduced setup overhead and kept the codebase compact enough to reason about quickly.

### 2. Persistence that preserves formatting cleanly

Documents are stored in SQLite with:

- owner metadata
- HTML document content
- timestamps
- optional source filename

Sharing is modeled in a join table between documents and users. This keeps the schema simple while still demonstrating real ownership and access rules.

### 3. A lightweight but usable editor

The editor uses a `contenteditable` surface with a formatting toolbar for:

- bold
- italic
- underline
- headings
- bulleted lists
- numbered lists

I used `document.execCommand` intentionally here. It is not the long-term architecture I would choose for a production editor, but it is a pragmatic option for a timed take-home because it avoids adding a large editor dependency while still producing a coherent editing flow.

## Request flow

### Dashboard

- Auth is simulated with seeded users
- The dashboard shows separate owned and shared document sections
- Users can create blank documents or import a file into a new document

### Editor

- A document page loads the stored HTML into the editor
- Toolbar actions update the rich-text content in place
- Save writes the title and HTML back through a JSON endpoint
- Owners can share the document with other seeded users

### Sharing

- Every document has exactly one owner
- The owner can grant access to other users
- Shared users can open and edit the document
- Only the owner can share it further

## Validation and error handling

- Empty titles are rejected on save
- Oversized uploads are rejected
- Unsupported file types are rejected
- Missing documents and unauthorized access return explicit error pages

## Testing

I added automated coverage around the highest-value flows:

- create a document
- save rich-text content
- share to another user
- import markdown into a new editable document

## What I would do with another 2-4 hours

- Replace `execCommand` with a modern editor library like TipTap or Slate
- Add share revocation and view-only/editor roles
- Harden HTML sanitization for untrusted users
- Add document search and recent activity
- Move deployment persistence to Postgres or a mounted production disk
