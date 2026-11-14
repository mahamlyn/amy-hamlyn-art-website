from __future__ import annotations

import os
import shutil
import sys
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

BASE_DIR = Path(__file__).resolve().parents[1]
DIST_DIR = BASE_DIR / "dist"
sys.path.insert(0, str(BASE_DIR))

from app import app, load_blog_posts


class BasePathRewriter(HTMLParser):
    def __init__(self, base_path: str):
        super().__init__(convert_charrefs=False)
        self.base_path = base_path
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.parts.append(self._render_tag(tag, attrs, self_closing=False))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.parts.append(self._render_tag(tag, attrs, self_closing=True))

    def handle_endtag(self, tag: str) -> None:
        self.parts.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_entityref(self, name: str) -> None:
        self.parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.parts.append(f"&#{name};")

    def handle_comment(self, data: str) -> None:
        self.parts.append(f"<!--{data}-->")

    def handle_decl(self, decl: str) -> None:
        self.parts.append(f"<!{decl}>")

    def handle_pi(self, data: str) -> None:
        self.parts.append(f"<?{data}>")

    def _render_tag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
        self_closing: bool,
    ) -> str:
        rendered_attrs = []
        for name, value in attrs:
            if value is None:
                rendered_attrs.append(name)
                continue
            if name in {"href", "src"}:
                value = self._rewrite_url(value)
            rendered_attrs.append(f'{name}="{escape(value, quote=True)}"')
        suffix = " />" if self_closing else ">"
        return f"<{tag}{''.join(f' {attr}' for attr in rendered_attrs)}{suffix}"

    def _rewrite_url(self, value: str) -> str:
        parsed = urlsplit(value)
        path = parsed.path
        if parsed.scheme or parsed.netloc or not path.startswith("/"):
            return value
        if self.base_path and (path == self.base_path or path.startswith(f"{self.base_path}/")):
            return value

        if path == "/":
            path = f"{self.base_path}/" if self.base_path else "/"
        else:
            path = f"{self.base_path}{path}"
            if "." not in path.rsplit("/", 1)[-1]:
                path += "/"
        return urlunsplit((parsed.scheme, parsed.netloc, path, parsed.query, parsed.fragment))


def rewrite_html(html: str, base_path: str) -> str:
    parser = BasePathRewriter(base_path)
    parser.feed(html)
    parser.close()
    return "".join(parser.parts)


def main() -> None:
    base_path = os.environ.get("PAGES_BASE_PATH", f"/{BASE_DIR.name}").strip()
    base_path = f"/{base_path.strip('/')}" if base_path.strip("/") else ""

    routes = [
        ("/", Path("index.html")),
        ("/about", Path("about/index.html")),
        ("/gallery", Path("gallery/index.html")),
        ("/exhibitions", Path("exhibitions/index.html")),
        ("/blog", Path("blog/index.html")),
        ("/contact", Path("contact/index.html")),
    ]
    routes.extend(
        (f"/blog/{post['slug']}", Path("blog") / post["slug"] / "index.html")
        for post in load_blog_posts()
    )

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)

    with app.test_client() as client:
        for route, output_path in routes:
            response = client.get(route)
            if response.status_code != 200:
                raise RuntimeError(f"Static export failed for {route}: {response.status_code}")
            destination = DIST_DIR / output_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(
                rewrite_html(response.get_data(as_text=True), base_path),
                encoding="utf-8",
            )

    shutil.copytree(BASE_DIR / "static", DIST_DIR / "static")
    (DIST_DIR / ".nojekyll").touch()
    print(f"Exported {len(routes)} pages to {DIST_DIR}")


if __name__ == "__main__":
    main()