from __future__ import annotations

import html
import re
from pathlib import Path

SOURCE_DIR = Path(r"E:\Code\artbyamyoz")
DEST_DIR = Path(r"E:\Code\amy-hamlyn-art-website\content\blog")


def clean_text(value: str) -> str:
    value = html.unescape(value)
    value = value.replace("&nbsp;", " ").replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def strip_tags(value: str) -> str:
    value = re.sub(r"(?is)<script.*?</script>", " ", value)
    value = re.sub(r"(?is)<style.*?</style>", " ", value)
    value = re.sub(r"(?is)<[^>]+>", " ", value)
    return clean_text(value)


def convert_inline(value: str) -> str:
    value = re.sub(r"(?is)<a\s+href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", lambda m: f"[{strip_tags(m.group(2))}]({m.group(1)})", value)
    value = re.sub(r"(?is)<strong[^>]*>(.*?)</strong>", r"**\1**", value)
    value = re.sub(r"(?is)<b[^>]*>(.*?)</b>", r"**\1**", value)
    value = re.sub(r"(?is)<em[^>]*>(.*?)</em>", r"*\1*", value)
    value = re.sub(r"(?is)<i[^>]*>(.*?)</i>", r"*\1*", value)
    value = re.sub(r"(?is)<br\s*/?>", "\n", value)
    value = re.sub(r"(?is)<[^>]+>", " ", value)
    value = html.unescape(value)
    value = value.replace("&nbsp;", " ")
    value = re.sub(r"\n{3,}", "\n\n", value)
    return re.sub(r"\s+\n+\s+", "\n\n", value).strip()


def read_html_title(text: str) -> str:
    match = re.search(r"(?is)<h1\s+class=[\"']entry-title[\"'][^>]*>(.*?)</h1>", text)
    if not match:
        match = re.search(r"(?is)<title>(.*?)</title>", text)
        if not match:
            return "Untitled"
    return strip_tags(match.group(1))


def read_html_date(text: str) -> str:
    match = re.search(r"(?is)<time[^>]*class=[\"'][^\"']*entry-date[^\"']*[\"'][^>]*>(.*?)</time>", text)
    if match:
        return clean_text(match.group(1))
    for token in ("2026-06-30", "2026-04-30", "2026-02-03", "2025-11-30", "2025-11-01", "2025-10-01", "2025-08-01", "2025-06-30", "2025-02-03", "2025-01-01"):
        if token in text:
            return token
    return ""


def extract_entry_body(text: str) -> str:
    pattern = r"(?is)<div\s+class=[\"']entry-content[\"'][^>]*>(.*?)(?:</div>\s*</div>\s*<!--\s*\.entry-content\s*-->|</div>\s*<!--\s*\.entry-content\s*-->|</div>)"
    match = re.search(pattern, text)
    if not match:
        match = re.search(r"(?is)<div\s+class=[\"']entry-content[\"'][^>]*>(.*)</div>", text)
    if not match:
        return ""
    body = match.group(1)

    body = re.sub(r"(?is)<figure[^>]*>.*?<img\s+[^>]*src=[\"']([^\"']+)[\"'][^>]*alt=[\"']([^\"']*)[\"'][^>]*>.*?</figure>", lambda m: f"\n\n![{m.group(2) or 'Image'}]({m.group(1)})\n\n", body)
    body = re.sub(r"(?is)<figure[^>]*>.*?<img\s+[^>]*src=[\"']([^\"']+)[\"'][^>]*>.*?</figure>", lambda m: f"\n\n![]({m.group(1)})\n\n", body)
    body = re.sub(r"(?is)<img\s+[^>]*src=[\"']([^\"']+)[\"'][^>]*alt=[\"']([^\"']*)[\"'][^>]*>", lambda m: f"\n\n![{m.group(2) or 'Image'}]({m.group(1)})\n\n", body)
    body = re.sub(r"(?is)<img\s+[^>]*src=[\"']([^\"']+)[\"'][^>]*>", lambda m: f"\n\n![]({m.group(1)})\n\n", body)
    body = re.sub(r"(?is)<p\s+class=[\"']wp-block-paragraph[\"'][^>]*>(.*?)</p>", lambda m: "\n\n" + convert_inline(m.group(1)) + "\n\n", body)
    body = re.sub(r"(?is)<p[^>]*>(.*?)</p>", lambda m: "\n\n" + convert_inline(m.group(1)) + "\n\n", body)
    body = re.sub(r"(?is)<div\s+class=[\"']wp-block-image[\"'][^>]*>.*?</div>", "\n\n", body)
    body = re.sub(r"(?is)<figure[^>]*>(.*?)</figure>", lambda m: "\n\n" + convert_inline(m.group(1)) + "\n\n", body)
    body = re.sub(r"(?is)<figcaption[^>]*>(.*?)</figcaption>", lambda m: "\n\n" + convert_inline(m.group(1)) + "\n\n", body)
    body = re.sub(r"(?is)<a\s+href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", lambda m: f"[{strip_tags(m.group(2))}]({m.group(1)})", body)
    body = re.sub(r"(?is)<[^>]+>", " ", body)
    body = html.unescape(body)
    body = body.replace("&nbsp;", " ").replace("\xa0", " ")
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()


def create_markdown(html_path: Path):
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    title = read_html_title(text)
    date = read_html_date(text)
    body = extract_entry_body(text)
    if not body:
        return

    excerpt = re.sub(r"\s+", " ", body)[:180].strip()
    if len(body) > 180:
        excerpt += "…"

    output = (
        "---\n"
        + '{"title": "' + title.replace('"', '\\"') + '", "date": "' + date.replace('"', '\\"') + '", "excerpt": "' + excerpt.replace('"', '\\"') + '"}\n'
        + "---\n\n"
        + body + "\n"
    )
    out_path = DEST_DIR / f"{html_path.stem}.md"
    out_path.write_text(output, encoding="utf-8")
    print(f"Wrote {out_path.name}")


def main():
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    for html_file in sorted(SOURCE_DIR.glob("*.html")):
        if html_file.name.lower() == "index.html":
            continue
        create_markdown(html_file)


if __name__ == "__main__":
    main()
