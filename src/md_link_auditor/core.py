from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse
import re


INLINE_LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)(?:\s+[^)]*)?\)")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$")


@dataclass(frozen=True)
class MarkdownLink:
    label: str
    target: str
    line: int


@dataclass(frozen=True)
class AuditItem:
    source: str
    target: str
    status: str
    line: int


@dataclass(frozen=True)
class AuditReport:
    ok: bool
    items: list[AuditItem]


def _iter_markdown_without_code(text: str) -> list[tuple[int, str]]:
    in_fence = False
    cleaned: list[tuple[int, str]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        cleaned.append((line_number, re.sub(r"`[^`]*`", "", line)))
    return cleaned


def extract_links(markdown_text: str) -> list[MarkdownLink]:
    """Extract inline Markdown links, ignoring images and code spans/fences."""
    links: list[MarkdownLink] = []
    for line_number, line in _iter_markdown_without_code(markdown_text):
        for match in INLINE_LINK_RE.finditer(line):
            links.append(MarkdownLink(label=match.group(1), target=match.group(2), line=line_number))
    return links


def slugify_heading(heading: str) -> str:
    """Approximate GitHub's Markdown heading anchor style."""
    slug = heading.strip().lower()
    slug = re.sub(r"[^a-z0-9\s_-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def _heading_slugs(path: Path) -> set[str]:
    slugs: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = HEADING_RE.match(line)
        if match:
            slugs.add(slugify_heading(match.group(1)))
    return slugs


def _markdown_files(paths: list[str | Path]) -> list[Path]:
    files: list[Path] = []
    for item in paths:
        path = Path(item)
        if path.is_dir():
            files.extend(sorted(path.rglob("*.md")))
        elif path.is_file() and path.suffix.lower() in {".md", ".markdown"}:
            files.append(path)
    return sorted(dict.fromkeys(files))


def _is_non_file_scheme(target: str) -> bool:
    parsed = urlparse(target)
    return parsed.scheme not in {"", "file"}


def _resolve_target(source: Path, target: str) -> tuple[Path, str | None]:
    path_part, sep, fragment = target.partition("#")
    if path_part == "":
        target_path = source
    else:
        target_path = (source.parent / unquote(path_part)).resolve()
    return target_path, unquote(fragment) if sep else None


def audit_paths(paths: list[str | Path]) -> AuditReport:
    """Audit Markdown files for broken local links and missing anchors."""
    items: list[AuditItem] = []
    for source in _markdown_files(paths):
        text = source.read_text(encoding="utf-8")
        for link in extract_links(text):
            if _is_non_file_scheme(link.target):
                continue
            target_path, anchor = _resolve_target(source, link.target)
            if not target_path.exists():
                items.append(AuditItem(str(source), link.target, "missing_file", link.line))
                continue
            if anchor:
                slugs = _heading_slugs(target_path)
                if anchor not in slugs:
                    items.append(AuditItem(str(source), link.target, "missing_anchor", link.line))
                    continue
            items.append(AuditItem(str(source), link.target, "ok", link.line))

    ok = all(item.status == "ok" for item in items)
    return AuditReport(ok=ok, items=items)
