# checks/lang_attr.py
# Check 5: Missing or empty lang attribute on the <html> root element.
# WCAG 2.1 Success Criterion 3.1.1 — Language of Page (Level A)
# Screen readers use the lang attribute to select the correct language
# profile and pronunciation rules. A missing lang attribute means the
# screen reader guesses — often incorrectly.

from bs4 import BeautifulSoup
from utils.logger import masLog
import config
METADATA = {
    "name":     "Language Attribute",
    "wcag":     "3.1.1",
    "level":    "A",
    "severity": config.SEVERITY_CRITICAL,
    "fix_hint": 'Add a lang attribute to the <html> element — for example: <html lang="en">.',
}

def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Check that the <html> element has a non-empty lang attribute.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url (str):            Optional URL of the document being checked.

    Returns:
        list: A list containing one finding if lang is missing or empty,
              or an empty list if the check passes.
    """

    masLog(f"Running check: {METADATA['name']}")

    findings = []

    # soup.find("html") locates the root <html> element.
    # In a well-formed document this always exists, but we handle
    # the None case defensively to avoid a crash on malformed input.
    html_tag = soup.find("html")

    if html_tag is None:
        # The document has no <html> tag at all — severely malformed.
        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  "Document has no <html> element — lang attribute cannot be evaluated",
            "element":  "",
            "fix_hint": METADATA["fix_hint"],
            "url":      url,
        })
        masLog("Lang check: no <html> element found", level="warning")
        return findings

    # html_tag.get("lang") returns the lang attribute value, or None if absent.
    lang = html_tag.get("lang")

    if lang is None:
        # The attribute is completely absent.
        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  '<html> element is missing the lang attribute (e.g. lang="en")',
            "element":  str(html_tag),
            "fix_hint": METADATA["fix_hint"],
            "url":      url,
        })

    elif lang.strip() == "":
        # The attribute exists but is empty: lang=""
        # An empty lang is treated the same as no lang by screen readers.
        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  '<html> element has an empty lang attribute — must specify a language (e.g. lang="en")',
            "element":  str(html_tag),
            "fix_hint": METADATA["fix_hint"],
            "url":          url,
        })

    if findings:
        masLog("Lang check: 1 issue found", level="warning")
    else:
        masLog(f"Lang check: passed — lang=\"{lang}\"")

    return findings
