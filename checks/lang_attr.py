# checks/lang_attr.py
# Check 5: Missing or empty lang attribute on the <html> root element.
# WCAG 2.1 Success Criterion 3.1.1 — Language of Page (Level A)
# Screen readers use the lang attribute to select the correct language
# profile and pronunciation rules. A missing lang attribute means the
# screen reader guesses — often incorrectly.

from bs4 import BeautifulSoup
from utils.logger import masLog

def check_lang_attr(soup: BeautifulSoup) -> list:
    """
    Check that the <html> element has a non-empty lang attribute.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.

    Returns:
        list: A list containing one finding if lang is missing or empty,
              or an empty list if the check passes.
    """

    masLog("Running check: lang attribute on <html> element")

    findings = []

    # soup.find("html") locates the root <html> element.
    # In a well-formed document this always exists, but we handle
    # the None case defensively to avoid a crash on malformed input.
    html_tag = soup.find("html")

    if html_tag is None:
        # The document has no <html> tag at all — severely malformed.
        findings.append({
            "check": "Language Attribute",
            "wcag": "3.1.1",
            "level": "A",
            "severity": "error",
            "message": "Document has no <html> element — lang attribute cannot be evaluated"
        })
        masLog("Lang check: no <html> element found", level="warning")
        return findings

    # html_tag.get("lang") returns the lang attribute value, or None if absent.
    lang = html_tag.get("lang")

    if lang is None:
        # The attribute is completely absent.
        findings.append({
            "check": "Language Attribute",
            "wcag": "3.1.1",
            "level": "A",
            "severity": "error",
            "message": '<html> element is missing the lang attribute (e.g. lang="en")'
        })

    elif lang.strip() == "":
        # The attribute exists but is empty: lang=""
        # An empty lang is treated the same as no lang by screen readers.
        findings.append({
            "check": "Language Attribute",
            "wcag": "3.1.1",
            "level": "A",
            "severity": "critical",
            "message": '<html> element has an empty lang attribute — must specify a language (e.g. lang="en")'
        })

    if findings:
        masLog("Lang check: 1 issue found", level="warning")
    else:
        masLog(f"Lang check: passed — lang=\"{lang}\"")

    return findings
