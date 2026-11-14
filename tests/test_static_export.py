import unittest

from scripts.build_static_site import rewrite_html


class StaticExportUrlTests(unittest.TestCase):
    def test_external_urls_are_not_rewritten(self):
        source = '<link href="https://fonts.googleapis.com/css2?family=Example">'

        rewritten = rewrite_html(source, "/amy-hamlyn-art-website")

        self.assertIn('href="https://fonts.googleapis.com/css2?family=Example"', rewritten)

    def test_local_routes_receive_pages_base_path(self):
        source = '<a href="/about">About</a>'

        rewritten = rewrite_html(source, "/amy-hamlyn-art-website")

        self.assertIn('href="/amy-hamlyn-art-website/about/"', rewritten)