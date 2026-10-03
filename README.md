# Amy Hamlyn Art

A lightweight Flask website for an artist portfolio and studio journal.

## Features
- Modern landing page with elegant, editorial styling
- About section written as Markdown
- Gallery with image cards and artwork descriptions
- Upcoming exhibitions section
- Blog section powered by Markdown posts
- Easy maintenance: update content in the `content/` folder without editing templates

## Project structure
- `app.py` – Flask app and content loaders
- `content/about.md` – About page content
- `content/gallery/*.md` – gallery item content
- `content/exhibitions/*.md` – exhibition information
- `content/blog/*.md` – blog posts
- `templates/` – HTML templates
- `static/` – CSS and image assets

## Run locally
1. Open a terminal in this folder.
2. Create a virtual environment if needed.
3. Install dependencies:
   `pip install -r requirements.txt`
4. Start the app:
   `python app.py`
5. Open the site in your browser at `http://127.0.0.1:5000`

## Updating content
Add or edit Markdown files in `content/`:
- About: `content/about.md`
- Gallery items: `content/gallery/*.md`
- Exhibitions: `content/exhibitions/*.md`
- Blog posts: `content/blog/*.md`

Each Markdown file can include YAML front matter like:

```yaml
---
title: "Example title"
date: "12 October 2026"
excerpt: "Short summary"
---
```

This keeps the site easy to maintain and update without needing web development knowledge.