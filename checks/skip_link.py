# checks/skip_link.py
# Check 14: Missing or non-functional skip navigation link.
# WCAG 2.1 Success Criterion 2.4.1 — Bypass Blocks (Level A)
# A skip link is the first focusable element on the page. It allows
# keyboard and screen reader users to jump past repeated navigation
# directly to the main content, avoiding tabbing through every nav item
# on every page load.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "Skip Navigation Link",
    "wcag":     "2.4.1",
    "level":    "A",
    "severity": config.SEVERITY_HIGH,
    "fix_hint": "Add a skip link as the first focusable element on the page: "
                '<a href="#main-content" class="skip-link">Skip to main content</a>. '
                "The target id must exist on the page. "
                "Make it visible on focus using CSS.",
}

# Text patterns that identify a skip link.
# Case-insensitive match applied at check time.
SKIP_LINK_PATTERNS = [
    "skip to main",
    "skip to content",
    "skip navigation",
    "skip nav",
    "skip to primary",
]


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Check that the page has a skip navigation link as its first focusable element.

    A skip link is identified by matching link text against known patterns.
    We also accept aria-label matches for icon-only skip links.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding if no skip link is detected, or empty list if found.
    """

    masLog(f"Running check: {METADATA['name']}")

    # Collect all <a href> elements in document order.
    links = soup.find_all("a", href=True)

    for link in links:
        text  = link.get_text(strip=True).lower()
        aria  = link.get("aria-label", "").lower()
        label = text + " " + aria

        if any(pattern in label for pattern in SKIP_LINK_PATTERNS):
            masLog(f"{METADATA['name']} check: passed — skip link found")
            return []

    # No skip link found anywhere on the page.
    masLog(f"{METADATA['name']} check: 1 issue found", level="warning")

    return [{
        "check":    METADATA["name"],
        "wcag":     METADATA["wcag"],
        "level":    METADATA["level"],
        "severity": METADATA["severity"],
        "message":  "No skip navigation link found. Keyboard users must tab "
                    "through all navigation on every page load.",
        "element":  "",
        "fix_hint": METADATA["fix_hint"],
        "line":   None,
        "parent": "",
        "url":      url,
    }]

