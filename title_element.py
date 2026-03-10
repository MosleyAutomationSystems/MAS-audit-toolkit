# checks/title_element.py
# Check 11: Missing, empty, or duplicate <title> element.
# WCAG 2.1 Success Criterion 2.4.2 — Page Titled (Level A)
# The <title> element is the first thing a screen reader announces
# when a page loads. It also appears in browser tabs and history.
# A missing or empty title leaves users with no page context.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "Page Title",
    "wcag":     "2.4.2",
    "level":    "A",
    "severity": config.SEVERITY_CRITICAL,
    "fix_hint": "Add a descriptive <title> element inside <head>. "
                "It should identify the page and the site — for example: "
                "<title>Menu — Glass House Bar GR</title>.",
}


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Check that the page has exactly one non-empty <title> element.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: A list of finding dicts, or an empty list if the check passes.
    """

    masLog(f"Running check: {METADATA['name']}")

    findings = []

    title_tags = soup.find_all("title")

    if len(title_tags) == 0:
        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  "Page has no <title> element — screen readers and "
                        "browser tabs will have no page identifier.",
            "element":  "",
            "fix_hint": METADATA["fix_hint"],
            "url":      url,
        })

    elif len(title_tags) > 1:
        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  f"Page has {len(title_tags)} <title> elements — "
                        "there must be exactly one.",
            "element":  str(title_tags[0]),
            "fix_hint": METADATA["fix_hint"],
            "url":      url,
        })

    else:
        # Exactly one title tag — check it is not empty or whitespace only.
        title_text = title_tags[0].get_text(strip=True)
        if not title_text:
            findings.append({
                "check":    METADATA["name"],
                "wcag":     METADATA["wcag"],
                "level":    METADATA["level"],
                "severity": METADATA["severity"],
                "message":  "<title> element is present but empty — "
                            "it must contain a descriptive page name.",
                "element":  str(title_tags[0]),
                "fix_hint": METADATA["fix_hint"],
                "url":      url,
            })

    if findings:
        masLog(f"{METADATA['name']} check: {len(findings)} issue(s) found",
               level="warning")
    else:
        masLog(f"{METADATA['name']} check: passed")

    return findings
