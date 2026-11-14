from __future__ import annotations

import os
import secrets
from datetime import datetime
from pathlib import Path

import bleach
import markdown
import yaml
from flask import Flask, render_template
from markupsafe import Markup
from flask_wtf.csrf import CSRFProtect

BASE_DIR = Path(__file__).resolve().parent
CONTENT_DIR = BASE_DIR / "content"
BLOG_DATE_FORMATS = ("%Y-%m-%d", "%B %d, %Y", "%d %B %Y")
MARKDOWN_TAGS = {
    "a", "abbr", "b", "blockquote", "br", "code", "dd", "del", "div", "dl",
    "dt", "em", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "img", "li",
    "ol", "p", "pre", "s", "span", "strong", "sub", "sup", "table", "tbody",
    "td", "th", "thead", "tr", "ul",
}
MARKDOWN_ATTRIBUTES = {
    "a": ["href", "title"],
    "img": ["src", "alt", "title"],
    "li": ["value"],
    "ol": ["start"],
    "td": ["colspan", "rowspan"],
    "th": ["colspan", "rowspan"],
}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
CSRFProtect(app)


def render_markdown(body: str) -> Markup:
    rendered = markdown.markdown(body, extensions=["extra", "sane_lists"])
    sanitized = bleach.clean(
        rendered,
        tags=MARKDOWN_TAGS,
        attributes=MARKDOWN_ATTRIBUTES,
        protocols={"http", "https", "mailto"},
        strip=True,
        strip_comments=True,
    )
    return Markup(sanitized)


def load_markdown_file(path: Path):
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            meta = yaml.safe_load(parts[1].strip()) or {}
            body = parts[2].strip()
            return meta, body
    return {}, text


def load_blog_posts():
    posts = []
    for path in sorted((CONTENT_DIR / "blog").glob("*.md")):
        meta, body = load_markdown_file(path)
        posts.append({
            "slug": path.stem,
            "title": meta.get("title", path.stem.replace("-", " ").title()),
            "date": meta.get("date", ""),
            "excerpt": meta.get("excerpt", ""),
            "content": render_markdown(body),
        })
    posts.sort(key=_blog_post_date, reverse=True)
    return posts


def _blog_post_date(post):
    value = str(post["date"])
    for date_format in BLOG_DATE_FORMATS:
        try:
            return datetime.strptime(value, date_format)
        except ValueError:
            continue
    return datetime.min


def load_gallery_items():
    items = []
    for path in sorted((CONTENT_DIR / "gallery").glob("*.md")):
        meta, body = load_markdown_file(path)
        items.append({
            "slug": path.stem,
            "title": meta.get("title", path.stem.replace("-", " ").title()),
            "image": meta.get("image", "/static/images/gallery/default.svg"),
            "medium": meta.get("medium", "Mixed media"),
            "dimensions": meta.get("dimensions", ""),
            "description": render_markdown(body),
        })
    return items


def load_exhibitions():
    exhibitions = []
    for path in sorted((CONTENT_DIR / "exhibitions").glob("*.md")):
        meta, body = load_markdown_file(path)
        exhibitions.append({
            "slug": path.stem,
            "title": meta.get("title", path.stem.replace("-", " ").title()),
            "date": meta.get("date", ""),
            "location": meta.get("location", ""),
            "content": render_markdown(body),
        })
    return exhibitions


def load_about():
    path = CONTENT_DIR / "about.md"
    if not path.exists():
        return "<p>Tell the story of your practice here.</p>"
    _, body = load_markdown_file(path)
    return render_markdown(body)


@app.route("/")
def index():
    return render_template(
        "index.html",
        about_html=load_about(),
        gallery_items=load_gallery_items(),
        exhibitions=load_exhibitions(),
        blog_posts=load_blog_posts()[:3],
    )


@app.route("/blog")
def blog_index():
    return render_template("blog.html", blog_posts=load_blog_posts())


@app.route("/blog/<slug>")
def blog_post(slug):
    post = None
    for item in load_blog_posts():
        if item["slug"] == slug:
            post = item
            break
    if post is None:
        return "Post not found", 404
    return render_template("post.html", post=post)


@app.route("/gallery")
def gallery_page():
    return render_template("gallery.html", gallery_items=load_gallery_items())


@app.route("/about")
def about_page():
    return render_template("about.html", about_html=load_about())


@app.route("/exhibitions")
def exhibitions_page():
    return render_template("exhibitions.html", exhibitions=load_exhibitions())


@app.route("/contact")
def contact_page():
    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=5000)
