from __future__ import annotations

from pathlib import Path

import markdown
import yaml
from flask import Flask, render_template

BASE_DIR = Path(__file__).resolve().parent
CONTENT_DIR = BASE_DIR / "content"

app = Flask(__name__)


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
            "content": markdown.markdown(body, extensions=["extra", "sane_lists"]),
        })
    return posts


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
            "description": markdown.markdown(body, extensions=["extra", "sane_lists"]),
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
            "content": markdown.markdown(body, extensions=["extra", "sane_lists"]),
        })
    return exhibitions


def load_about():
    path = CONTENT_DIR / "about.md"
    if not path.exists():
        return "<p>Tell the story of your practice here.</p>"
    _, body = load_markdown_file(path)
    return markdown.markdown(body, extensions=["extra", "sane_lists"])


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
    app.run(debug=True, host="127.0.0.1", port=5000)
