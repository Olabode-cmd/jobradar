"""Text cleanup for scraped descriptions."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Any

MAX_DESCRIPTION_CHARS = 20_000
_BLOCK_TAGS = {"p", "br", "div", "li", "ul", "ol", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}
_SKIPPED_TAGS = {"script", "style"}
_MOJIBAKE = re.compile("[\u00c2\u00c3\u00e2][\u0080-\u00bf]")


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _SKIPPED_TAGS:
            self._skip_depth += 1
        elif tag in _BLOCK_TAGS:
            self.parts.append("\n- " if tag == "li" else "\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIPPED_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
        elif tag in _BLOCK_TAGS and tag != "li":
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self.parts.append(data)


def fix_mojibake(text: str) -> str:
    """Undo UTF-8 text that an upstream feed double-encoded as Latin-1 ("\u00e2\u0080\u0094" for an em dash)."""
    if not _MOJIBAKE.search(text):
        return text
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def html_to_text(value: Any) -> str | None:
    """Plain text from an HTML or text description: tags dropped, blocks become lines."""
    if not value:
        return None
    text = fix_mojibake(str(value))
    if "<" in text:
        extractor = _TextExtractor()
        extractor.feed(text)
        extractor.close()
        text = "".join(extractor.parts)
    lines = [" ".join(line.split()) for line in text.splitlines()]
    collapsed = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    return collapsed[:MAX_DESCRIPTION_CHARS] or None
