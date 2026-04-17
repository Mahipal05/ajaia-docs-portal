from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path

from app import create_app


class DocSprintTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "test-portal.db"
        self.app = create_app(
            {
                "TESTING": True,
                "DATABASE": str(database_path),
                "SECRET_KEY": "test-secret",
            }
        )
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def login(self, user_id: int) -> None:
        response = self.client.post("/login", data={"user_id": user_id})
        self.assertEqual(response.status_code, 302)

    def test_owner_can_create_save_and_share_document(self) -> None:
        self.login(1)

        response = self.client.post("/documents", data={"title": "Launch memo"})
        self.assertEqual(response.status_code, 302)

        document_id = int(response.headers["Location"].rstrip("/").split("/")[-1])

        save_response = self.client.post(
            f"/api/documents/{document_id}/save",
            json={
                "title": "Launch memo",
                "content_html": "<h1>Kickoff</h1><p>Share this with Ava.</p>",
            },
        )
        self.assertEqual(save_response.status_code, 200)
        self.assertEqual(save_response.json["title"], "Launch memo")

        share_response = self.client.post(
            f"/documents/{document_id}/share",
            data={"target_user_id": 2},
            follow_redirects=True,
        )
        self.assertEqual(share_response.status_code, 200)
        self.assertIn(b"Access granted", share_response.data)

        self.client.post("/logout")
        self.login(2)

        dashboard_response = self.client.get("/")
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertIn(b"Launch memo", dashboard_response.data)
        self.assertIn(b"Shared with you", dashboard_response.data)

        editor_response = self.client.get(f"/documents/{document_id}")
        self.assertEqual(editor_response.status_code, 200)
        self.assertIn(b"Share this with Ava.", editor_response.data)

    def test_markdown_import_creates_editable_document(self) -> None:
        self.login(1)

        import_response = self.client.post(
            "/documents/import",
            data={
                "title": "",
                "import_file": (io.BytesIO(b"# Heading\n\n- first\n- second"), "brief.md"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(import_response.status_code, 302)

        document_id = int(import_response.headers["Location"].rstrip("/").split("/")[-1])
        editor_response = self.client.get(f"/documents/{document_id}")

        self.assertEqual(editor_response.status_code, 200)
        self.assertIn(b"<h1>Heading</h1>", editor_response.data)
        self.assertIn(b"<li>first</li>", editor_response.data)


if __name__ == "__main__":
    unittest.main()
