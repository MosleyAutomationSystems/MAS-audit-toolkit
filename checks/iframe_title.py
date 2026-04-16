# checks/iframe_title.py
# Check 21: iframe elements missing title attribute.
# WCAG 2.1 Success Criterion 4.1.2 — Name, Role, Value (Level A)
#
# The <iframe> element embeds external content — maps, videos, forms,
# payment widgets, social media feeds — into a page. Screen readers
# announce iframes as embedded regions. Without a title attribute,
# the screen reader announces "frame" with no context, leaving blind
# users unable to determine whether to enter or skip the iframe.
#
# A descriptive title attribute gives the iframe a programmatic label
# that screen readers read before the user decides to navigate into it.
# Example: <iframe title="Google Maps — MAS office location" ...>

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "iframe Title Check",
    "wcag":     "4.1.2",
    "level":    "A",
    "severity": config.SEVERITY_HIGH,
    "fix_hint": "Add a descriptive title attribute to every <iframe> element. "
                "The title should describe the purpose of the embedded content, "
                "not its source. Good: title=\"Google Maps — store location\". "
                "Bad: title=\"iframe\" or title=\"map\". "
                "If the iframe contains decorative or non-essential content, "
                "use title=\"\" and add aria-hidden=\"true\" to remove it from "
                "the accessibility tree entirely.",
}

GENERIC_TITLES = {
    "iframe", "frame", "embed", "embedded", "content",
    "widget", "plugin", "untitled", "no title", "none",
}


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Check all <iframe> elements for a descriptive title attribute.

    Flags iframes that are:
      - Missing the title attribute entirely
      - Have an empty title (whitespace only)
      - Have a generic title that provides no useful context

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding per <iframe> missing a valid title.
    """

    masLog(f"Running check: {METADATA['name']}")

    findings = []

    iframes = soup.find_all("iframe")

    if not iframes:
        masLog(f"{METADATA['name']} check: passed — no <iframe> elements found")
        return []

    for iframe in iframes:
        # Skip iframes explicitly marked as decorative.
        aria_hidden = iframe.get("aria-hidden", "").strip().lower()
        if aria_hidden == "true":
            continue

        title     = iframe.get("title", "").strip()
        title_low = title.lower()

        if title and title_low not in GENERIC_TITLES:
            continue

        if not title:
            issue = "missing title attribute" if iframe.get("title") is None else "empty title attribute"
        else:
            issue = f"generic title \"{title}\" provides no useful context"

        src    = iframe.get("src", "[no src]")
        frm_id = iframe.get("id", "")
        el_ref = (
            f'id="{frm_id}"' if frm_id
            else f'src="{src[:60]}"'
        )

        masLog(
            f"{METADATA['name']} check: <iframe> {el_ref} has {issue}",
            level="warning"
        )

        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  f"<iframe> has {issue} — screen readers will announce "
                        f"\"frame\" with no context. Users cannot determine whether "
                        f"to enter or skip this embedded content. {el_ref}",
            "element":  str(iframe)[:120],
            "fix_hint": METADATA["fix_hint"],
            "line":   getattr(iframe, 'sourceline', None),
            "parent": "",
            "url":      url,
        })

    if not findings:
        masLog(f"{METADATA['name']} check: passed — all <iframe> elements have valid titles")

    return findings

