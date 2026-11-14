import unittest

from app import app, load_blog_posts


class PageRouteMethodTests(unittest.TestCase):
    def setUp(self):
        self.previous_testing = app.config.get("TESTING", False)
        self.previous_csrf = app.config.get("WTF_CSRF_ENABLED", True)
        app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        self.client = app.test_client()
        self.page_paths = [
            "/",
            "/blog",
            f"/blog/{load_blog_posts()[0]['slug']}",
            "/gallery",
            "/about",
            "/exhibitions",
            "/contact",
        ]

    def tearDown(self):
        app.config.update(
            TESTING=self.previous_testing,
            WTF_CSRF_ENABLED=self.previous_csrf,
        )

    def test_all_page_routes_allow_get(self):
        for path in self.page_paths:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_all_page_routes_reject_post(self):
        for path in self.page_paths:
            with self.subTest(path=path):
                self.assertEqual(self.client.post(path).status_code, 405)


if __name__ == "__main__":
    unittest.main()