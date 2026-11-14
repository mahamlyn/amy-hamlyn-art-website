import unittest

from app import render_markdown


class MarkdownSanitizationTests(unittest.TestCase):
    def test_preserves_markdown_formatting_and_images(self):
        rendered = str(render_markdown("**Bold**\n\n![Artwork](/static/images/art.png)"))

        self.assertIn("<strong>Bold</strong>", rendered)
        self.assertIn('<img alt="Artwork" src="/static/images/art.png">', rendered)

    def test_removes_script_tags_event_handlers_and_unsafe_urls(self):
        rendered = str(render_markdown(
            '<script>alert(1)</script><img src="/art.png" onerror="alert(1)">'
            '<a href="javascript:alert(1)">link</a>'
        ))

        self.assertNotIn("<script", rendered.lower())
        self.assertNotIn("onerror", rendered.lower())
        self.assertNotIn("javascript:", rendered.lower())
        self.assertIn('<img src="/art.png">', rendered)
        self.assertIn(">link</a>", rendered)


if __name__ == "__main__":
    unittest.main()