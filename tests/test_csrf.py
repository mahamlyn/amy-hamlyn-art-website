import unittest

from app import app


def csrf_test_endpoint():
    return "accepted"


app.add_url_rule(
    "/__test/csrf",
    endpoint="csrf_test_endpoint",
    view_func=csrf_test_endpoint,
    methods=["POST"],
)


class CsrfProtectionTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_contact_page_get_remains_available(self):
        response = self.client.get("/contact")
        self.assertEqual(response.status_code, 200)

    def test_post_without_csrf_token_is_rejected(self):
        response = self.client.post("/__test/csrf")
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()