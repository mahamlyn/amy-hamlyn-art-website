import unittest

from app import app


class AboutAccessibilityTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_portrait_placeholder_uses_native_figure_caption(self):
        response = self.client.get("/about")
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('<figure class="about-portrait">', html)
        self.assertIn("<figcaption>Portrait to be added</figcaption>", html)
        self.assertNotIn('role="img"', html)


if __name__ == "__main__":
    unittest.main()