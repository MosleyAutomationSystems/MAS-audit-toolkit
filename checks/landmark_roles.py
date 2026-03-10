# checks/landmark_roles.py
# Check 13: Missing landmark regions on the page.
# WCAG 2.1 Success Criterion 1.3.6 — Identify Purpose (Level AAA)
# WCAG 2.1 Success Criterion 2.4.1 — Bypass Blocks (Level A)
# Landmark elements (main, nav, header, footer) allow screen reader
# users to jump directly to page sections without tabbing through
# every element. A page with no landmarks forces linear navigation.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "Landmark Roles",
    "wcag":     "2.4.1",
    "level":    "A",
    "severity": config.SEVERITY_HIGH,
    "fix_hint": "Add semantic landmark elements to the page structure: "
                "<main> for primary content, <nav> for navigation, "
                "<header> for the page header, <footer> for the page footer.",
}

# Landmarks we require and their ARIA role equivalents.
# Each entry: (tag_name, aria_role, description)
REQUIRED_LANDMARKS = [
    ("main",   "main",          "<main> — primary page content"),
    ("nav",    "navigation",    "<nav> — navigation region"),
    ("header", "banner",        "<header> — page header"),
    ("footer", "contentinfo",   "<footer> — page footer"),
]


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Check that the page contains the four required landmark regions.
    Accepts either a semantic HTML element or an element with the
    equivalent ARIA role attribute.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding per missing landmark, or empty list if all present.
    """

    masLog(f"Running check: {METADATA['name']}")

    findings = []

    for tag_name, aria_role, description in REQUIRED_LANDMARKS:
        # Accept the semantic element OR role= equivalent.
        found = (
            soup.find(tag_name) or
            soup.find(attrs={"role": aria_role})
        )

        if not found:
            findings.append({
                "check":    METADATA["name"],
                "wcag":     METADATA["wcag"],
                "level":    METADATA["level"],
                "severity": METADATA["severity"],
                "message":  f"Missing landmark: {description} — "
                            f"not found as a semantic element or role=\"{aria_role}\".",
                "element":  "",
                "fix_hint": METADATA["fix_hint"],
                "url":      url,
            })

    if findings:
        masLog(f"{METADATA['name']} check: {len(findings)} missing landmark(s) found",
               level="warning")
    else:
        masLog(f"{METADATA['name']} check: passed")

    return findings