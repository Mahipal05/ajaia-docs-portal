# AI Workflow Note

## AI tools used

- Codex / GPT-5 as a paired engineering assistant during implementation

## Where AI materially sped up the work

- Turning the assignment prompt into a scoped implementation plan
- Drafting the Flask app structure and route layout
- Accelerating first-pass UI copy and visual direction
- Generating an initial markdown import parser and test scaffolding
- Speeding up README and architecture note drafting so the product and documentation stayed aligned

## What I changed or rejected from AI-generated output

- I simplified the architecture away from a heavier SPA/editor-library setup because it was not justified for the timebox.
- I reworked the sharing model to keep ownership and access rules explicit in the database instead of hiding that logic in the UI.
- I tightened validation and error-handling paths rather than accepting broader generated assumptions.
- I kept file import intentionally limited to `.txt`, `.md`, and `.html` instead of over-claiming `.docx` support without reliable parsing in scope.

## How I verified correctness, UX quality, and reliability

- Added automated tests for the most important end-to-end flows: create, save, import, and share
- Manually checked that owned and shared documents render in distinct sections
- Verified that document HTML is persisted and reloads into the editor
- Reviewed the UI for clarity around supported file types, demo users, and sharing behavior
- Kept the implementation dependency-light to reduce setup and deployment risk

## Where AI was helpful but not authoritative

AI sped up scaffolding and drafting, but I treated it as a collaborator rather than a source of truth. Product cuts, data modeling, validation choices, and the final UX behavior were decided manually to stay aligned with the assignment goals.
