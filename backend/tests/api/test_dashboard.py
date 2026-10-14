import json
import tempfile
import unittest
from pathlib import Path

from app.api.app import create_app
from tests.api.asgi import request


class DashboardServingTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        self.dist = root / "dist"
        (self.dist / "assets").mkdir(parents=True)
        (self.dist / "index.html").write_text("<html>dashboard</html>", encoding="utf-8")
        (self.dist / "assets" / "app.js").write_text("console.log(1)", encoding="utf-8")
        (root / "secret.txt").write_text("top secret", encoding="utf-8")
        self.app = create_app(self.dist)

    def test_serves_index_at_the_root(self):
        status, _, body = request(self.app, "GET", "/")
        self.assertEqual((status, body), (200, b"<html>dashboard</html>"))

    def test_serves_static_assets(self):
        status, _, body = request(self.app, "GET", "/assets/app.js")
        self.assertEqual((status, body), (200, b"console.log(1)"))

    def test_client_side_routes_fall_back_to_index(self):
        status, _, body = request(self.app, "GET", "/inbox")
        self.assertEqual((status, body), (200, b"<html>dashboard</html>"))

    def test_unknown_api_paths_are_json_404s_not_the_dashboard(self):
        status, headers, body = request(self.app, "GET", "/api/nope")
        self.assertEqual(status, 404)
        self.assertIn("application/json", headers["content-type"])
        self.assertEqual(json.loads(body), {"detail": "Not found"})

    def test_real_api_routes_still_win(self):
        status, _, body = request(self.app, "GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["status"], "ok")

    def test_path_traversal_cannot_leave_the_build_directory(self):
        for path in ["/../secret.txt", "/assets/../../secret.txt", "/%2e%2e/secret.txt"]:
            with self.subTest(path=path):
                _, _, body = request(self.app, "GET", path)
                self.assertNotIn(b"top secret", body)

    def test_foreign_host_is_still_rejected(self):
        status, _, _ = request(self.app, "GET", "/", host="evil.example.com")
        self.assertEqual(status, 403)

    def test_no_build_means_no_dashboard_route(self):
        empty = Path(tempfile.mkdtemp())
        status, _, _ = request(create_app(empty), "GET", "/")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
