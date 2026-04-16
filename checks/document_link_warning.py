# checks/document_link_warning.py
# Check 34: Document file links without format warning.
# WCAG 2.1 Success Criterion 2.4.4 — Link Purpose (Level A)
#
# Links that download or open document files (.docx, .xlsx, .pptx, etc.)
# should warn users about the file format and approximate file size when
# possible. Without this warning, users may:
#   - Unexpectedly trigger a file download
#   - Open a file in an application they don't have installed
#   - Experience long waits for large file downloads on slow connections
#   - Be surprised when a non-HTML document opens in an external application
#
# This is especially important for screen reader users who navigate by
# links — they need to understand what activating a link will do before
# they activate it.
#
# The warning should indicate:
#   - The file format (Word document, Excel spreadsheet, PowerPoint, PDF)
#   - Ideally the file size if known
#
# Note: PDF links are already handled by check #9 (pdf_links.py).
# This check covers Office document formats and other common non-HTML files.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "Document Link Warning",
    "wcag":     "2.4.4",
    "level":    "A",
    "severity": config.SEVERITY_LOW,
    "fix_hint": "Add a format warning to links that open or download document files. "
                "Include the file type in the link text or aria-label. Examples: "
                "\"Download the annual report (Word document, 2MB)\", "
                "\"View the budget spreadsheet (Excel file)\", "
                "\"Download the presentation (PowerPoint, 5MB)\". "
                "For screen reader users, the format warning in the link text "
                "is the most reliable approach.",
}

# File extensions to flag and their human-readable format names.
DOCUMENT_FORMATS = {
    ".docx": "Word document",
    ".doc":  "Word document",
    ".xlsx": "Excel spreadsheet",
    ".xls":  "Excel spreadsheet",
    ".pptx": "PowerPoint presentation",
    ".ppt":  "PowerPoint presentation",
    ".odt":  "OpenDocument text",
    ".ods":  "OpenDocument spreadsheet",
    ".odp":  "OpenDocument presentation",
    ".rtf":  "RTF document",
    ".csv":  "CSV file",
}

# Warning phrases that indicate the format is communicated.
# Checked case-insensitively against link text and aria-label.
WARNING_PATTERNS = [
    "word", "excel", "spreadsheet", "powerpoint", "presentation",
    "document", "docx", "xlsx", "pptx", ".doc", ".xls", ".ppt",
    "odt", "ods", "odp", "rtf", "csv", "opens in", "download",
    "file", "mb", "kb",
]


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Check links to document files for a format warning.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding per document link missing a format warning.
    """

    masLog(f"Running check: {METADATA['name']}")

    findings = []

    for link in soup.find_all("a", href=True):
        href      = link.get("href", "").strip()
        href_lower = href.lower()

        # Identify the document format from the href extension.
        matched_ext    = None
        matched_format = None
        for ext, fmt in DOCUMENT_FORMATS.items():
            if href_lower.endswith(ext) or f"{ext}?" in href_lower:
                matched_ext    = ext
                matched_format = fmt
                break

        if not matched_ext:
            continue

        text       = link.get_text(strip=True)
        aria_label = link.get("aria-label", "")
        combined   = (text + " " + aria_label).lower()

        # Pass if a warning phrase is present.
        if any(pattern in combined for pattern in WARNING_PATTERNS):
            continue

        display_text = text[:40] if text else "[no text]"
        filename     = href.split("/")[-1].split("?")[0][:60]

        masLog(
            f"{METADATA['name']} check: {matched_ext} link has no format warning — {filename}",
            level="warning"
        )

        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  f"Link to {matched_format} ({matched_ext}) has no format warning. "
                        f"Users may not expect a file download or external application launch. "
                        f"Link text: \"{display_text}\", file: \"{filename}\"",
            "element":  str(link)[:120],
            "fix_hint": METADATA["fix_hint"],
            "line":   getattr(link, 'sourceline', None),
            "parent": "",
            "url":      url,
        })

    if not findings:
        masLog(f"{METADATA['name']} check: passed — all document links have format warnings")

    return findings

