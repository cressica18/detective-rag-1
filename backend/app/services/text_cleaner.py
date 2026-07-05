"""Text cleaner — normalizes and denoises raw parsed text."""
import re
from collections import Counter


def clean_pages(pages: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """Clean a list of (page, text) tuples."""
    if not pages:
        return pages
    # Detect repeated header/footer lines (present in >50% of pages)
    repeated = _find_repeated_lines(pages)
    cleaned = []
    for page_num, text in pages:
        text = _clean_text(text, repeated)
        if text.strip():
            cleaned.append((page_num, text))
    return cleaned if cleaned else pages


def _find_repeated_lines(pages: list[tuple[int, str]]) -> set[str]:
    """Find lines that appear in more than 50% of pages (likely headers/footers)."""
    if len(pages) < 3:
        return set()
    line_counter: Counter = Counter()
    for _, text in pages:
        seen_on_page = set()
        for line in text.splitlines():
            stripped = line.strip()
            if stripped and len(stripped) < 100:
                seen_on_page.add(stripped)
        for line in seen_on_page:
            line_counter[line] += 1
    threshold = len(pages) * 0.5
    return {line for line, count in line_counter.items() if count >= threshold}


def _clean_text(text: str, repeated_lines: set[str]) -> str:
    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        # Remove repeated header/footer lines
        if stripped in repeated_lines:
            continue
        # Remove page-number-only lines (e.g., "- 3 -", "Page 3", "3")
        if re.match(r"^[-–—]?\s*\d{1,3}\s*[-–—]?$", stripped):
            continue
        if re.match(r"^page\s+\d+\s*$", stripped, re.IGNORECASE):
            continue
        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)
    # Fix ligature artifacts from PDF
    text = text.replace("ﬁ", "fi").replace("ﬂ", "fl").replace("ﬀ", "ff")
    text = text.replace("ﬃ", "ffi").replace("ﬄ", "ffl").replace("ﬅ", "st")
    # Normalize quotes and dashes
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2013", "-").replace("\u2014", " - ")
    # Collapse excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()
