# checks/empty_links.py
# Check 7: Anchor elements with no accessible name.
# WCAG 2.1 Success Criterion 2.4.4 — Link Purpose (Level A)
# A screen reader announces a link by its accessible name — the visible
# text, aria-label, or aria-labelledby value. A link with none of these
# is announced as "link" with no context, leaving keyboard and screen
# reader users unable to determine its destination or purpose.

from bs4 import BeautifulSoup
from utils.logger import masLog

def check_empty_links(soup: BeautifulSoup) -> list:
    """
    Find all <a> elements that have no accessible name.

    An accessible name is present if ANY of these exist:
    1. Non-empty visible text content inside the element
    2. An aria-label attribute with non-empty value
    3. An aria-labelledby attribute pointing to another element
    4. A child <img> with a non-empty alt attribute

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.

    Returns:
        list: A list of finding dictionaries for each nameless link.
    """

    masLog("Running check: empty or nameless <a> elements")

    findings = []

    # Find all anchor tags that have an href attribute.
    # Anchors without href are not interactive links — they are fragment
    # targets or placeholders and do not need an accessible name.
    links = soup.find_all("a", href=True)

    masLog(f"Found {len(links)} <a href> element(s) to check")

    for link in links:

        # Check 1: aria-label
        if link.get("aria-label", "").strip():
            continue

        # Check 2: aria-labelledby
        if link.get("aria-labelledby", "").strip():
            continue

        # Check 3: visible text content.
        # get_text() strips all inner HTML and returns only visible characters.
        if link.get_text(strip=True):
            continue

        # Check 4: child <img> with non-empty alt text.
        # Icon-only links that use an image must give that image a descriptive alt.
        img = link.find("img")
        if img and img.get("alt", "").strip():
            continue

        # No accessible name found.
        href = link.get("href", "[no href]")

        findings.append({
            "check":    "Empty Link",
            "wcag":     "2.4.4",
            "level":    "A",
            "severity": "critical",
            "message":  (
                f'<a> has no accessible name — screen readers will announce '
                f'"link" with no context. href="{href}"'
            )
        })

    if findings:
        masLog(f"Empty link check: {len(findings)} issue(s) found", level="warning")
    else:
        masLog("Empty link check: passed — all links have accessible names")

    return findings
