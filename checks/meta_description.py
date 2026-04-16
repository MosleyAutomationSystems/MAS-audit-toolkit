# checks/meta_description.py
# Check 41: Missing or empty meta description tag.
# Mosley Standard — Operational (MS)
#
# The meta description tag provides a brief summary of a page's content.
# It is used by:
#   - Search engines to generate result snippets
#   - Screen readers and browser toolbars in some configurations
#   - Social media platforms when generating link previews
#
# While not a WCAG criterion, a missing meta description is an operational
# deficiency that affects discoverability and indirectly affects accessibility
# by reducing the ability of users to determine page relevance before visiting.
#
# This is an informational (INFO) finding — it does not block access
# but represents a best-practice gap that should be addressed.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "Meta Description Check",
    "wcag":     "MS",
    "level":    "MS",
    "severity": config.SEVERITY_INFO,
    "fix_hint": "Add a meta description tag to the <head> section of every page. "
                "Keep it between 50–160 characters. It should accurately summarize "
                "the page content in plain language. Example: "
                "<meta name=\"description\" content=\"MAS Accessibility Audit Toolkit "
                "— automated WCAG 2.1 AA checks for small business websites.\">. "
                "Each page should have a unique description.",
}


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Check for a non-empty meta description tag in the document head.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding if meta description is missing or empty.
    """

    masLog(f"Running check: {METADATA['name']}")

    # Find meta description tag.
    meta_desc = soup.find(
        "meta",
        attrs={"name": lambda v: v and v.strip().lower() == "description"}
    )

    if meta_desc is None:
        masLog(f"{METADATA['name']} check: missing meta description tag", level="warning")
        return [{
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  "Page is missing a <meta name=\"description\"> tag. "
                        "Search engines and some assistive tools use this to "
                        "summarize page content. Without it, search engines may "
                        "auto-generate an unhelpful snippet.",
            "element":  "<head>",
            "fix_hint": METADATA["fix_hint"],
            "line":   None,
            "parent": "",
            "url":      url,
        }]

    content = meta_desc.get("content", "").strip()

    if not content:
        masLog(f"{METADATA['name']} check: meta description is empty", level="warning")
        return [{
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  "Meta description tag is present but has an empty content "
                        "attribute. An empty description is equivalent to no description.",
            "element":  str(meta_desc)[:120],
            "fix_hint": METADATA["fix_hint"],
            "line":   getattr(meta_desc, 'sourceline', None),
            "parent": "",
            "url":      url,
        }]

    masLog(f"{METADATA['name']} check: passed — meta description found ({len(content)} chars)")
    return []

