from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path


SUPPORTED_EXTENSIONS = {".txt", ".md", ".html"}


class UnsupportedImportError(ValueError):
    pass


@dataclass(slots=True)
class ImportedDocument:
    suggested_title: str
    content_html: str


def title_from_filename(filename: str) -> str:
    stem = Path(filename).stem.strip() or "Imported document"
    spaced = re.sub(r"[_-]+", " ", stem)
    return spaced[:1].upper() + spaced[1:]


def import_file(filename: str, raw_bytes: bytes) -> ImportedDocument:
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise UnsupportedImportError(
            f"Unsupported file type. Please upload one of: {supported}."
        )

    decoded = raw_bytes.decode("utf-8", errors="ignore")
    if not decoded.strip():
        raise UnsupportedImportError("The uploaded file is empty.")

    if extension == ".md":
        content_html = markdown_to_html(decoded)
    elif extension == ".html":
        content_html = extract_body_html(decoded)
    else:
        content_html = plain_text_to_html(decoded)

    return ImportedDocument(
        suggested_title=title_from_filename(filename),
        content_html=content_html,
    )


def plain_text_to_html(text: str) -> str:
    blocks = [block.strip() for block in text.replace("\r\n", "\n").split("\n\n")]
    paragraphs: list[str] = []
    for block in blocks:
        if not block:
            continue
        escaped = "<br>".join(html.escape(line) for line in block.splitlines())
        paragraphs.append(f"<p>{escaped}</p>")
    return "".join(paragraphs) or "<p></p>"


def markdown_to_html(text: str) -> str:
    lines = text.replace("\r\n", "\n").split("\n")
    html_parts: list[str] = []
    in_ul = False
    in_ol = False
    paragraph_lines: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        if paragraph_lines:
            merged = " ".join(part.strip() for part in paragraph_lines if part.strip())
            html_parts.append(f"<p>{apply_inline_markdown(merged)}</p>")
            paragraph_lines = []

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            html_parts.append("</ul>")
            in_ul = False
        if in_ol:
            html_parts.append("</ol>")
            in_ol = False

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            close_lists()
            continue

        heading_match = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        unordered_match = re.match(r"^[-*]\s+(.*)$", stripped)
        ordered_match = re.match(r"^\d+\.\s+(.*)$", stripped)

        if heading_match:
            flush_paragraph()
            close_lists()
            level = len(heading_match.group(1))
            html_parts.append(
                f"<h{level}>{apply_inline_markdown(heading_match.group(2))}</h{level}>"
            )
            continue

        if unordered_match:
            flush_paragraph()
            if in_ol:
                html_parts.append("</ol>")
                in_ol = False
            if not in_ul:
                html_parts.append("<ul>")
                in_ul = True
            html_parts.append(f"<li>{apply_inline_markdown(unordered_match.group(1))}</li>")
            continue

        if ordered_match:
            flush_paragraph()
            if in_ul:
                html_parts.append("</ul>")
                in_ul = False
            if not in_ol:
                html_parts.append("<ol>")
                in_ol = True
            html_parts.append(f"<li>{apply_inline_markdown(ordered_match.group(1))}</li>")
            continue

        paragraph_lines.append(stripped)

    flush_paragraph()
    close_lists()
    return "".join(html_parts) or "<p></p>"


def apply_inline_markdown(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"__(.+?)__", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*(.+?)\*", r"<em>\1</em>", escaped)
    escaped = re.sub(r"_(.+?)_", r"<em>\1</em>", escaped)
    escaped = re.sub(r"`(.+?)`", r"<code>\1</code>", escaped)
    return escaped


def extract_body_html(text: str) -> str:
    body_match = re.search(r"<body[^>]*>(.*)</body>", text, flags=re.IGNORECASE | re.DOTALL)
    extracted = body_match.group(1) if body_match else text
    return extracted.strip() or "<p></p>"


def html_preview(content_html: str, limit: int = 150) -> str:
    collapsed = re.sub(r"<[^>]+>", " ", content_html)
    collapsed = html.unescape(re.sub(r"\s+", " ", collapsed)).strip()
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 1].rstrip() + "…"
