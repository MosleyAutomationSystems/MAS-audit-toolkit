# checks/patterns.py
# Check 15: Common accessibility anti-patterns.
# Detects recurring HTML patterns that consistently produce accessibility
# failures — generic link text, placeholder-as-label, onclick on non-
# interactive elements, missing table headers, and blank-target warnings.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "Accessibility Patterns",
    "wcag":     "2.4.4",
    "level":    "A",
    "severity": config.SEVERITY_HIGH,
    "fix_hint": "Replace generic link text with descriptive text. "
                "Remove placeholder-as-label patterns. "
                "Add scope attributes to table headers. "
                "Add rel='noreferrer' and a warning to blank-target links.",
}

# Generic link text patterns — convey no destination or purpose.
GENERIC_LINK_TEXT = [
    "click here", "here", "read more", "more", "learn more",
    "this link", "link", "details", "info", "continue",
]

# Input types that legitimately use placeholder without a visible label.
PLACEHOLDER_EXEMPT = {"submit", "reset", "button", "hidden", "image"}


def _check_generic_links(soup, url, findings):
    """Flag <a> elements whose visible text matches a generic pattern."""
    for link in soup.find_all("a", href=True):
        text = link.get_text(strip=True).lower()
        if text in GENERIC_LINK_TEXT:
            findings.append({
                "check":    METADATA["name"],
                "wcag":     "2.4.4",
                "level":    "A",
                "severity": config.SEVERITY_HIGH,
                "message":  f'Generic link text "{link.get_text(strip=True)}" — '
                            f'does not describe the link destination. '
                            f'href="{link.get("href", "")}"',
                "element":  str(link),
                "fix_hint": "Replace generic link text with a description of "
                            "the link destination — for example: "
                            '"Read our accessibility policy" instead of "Read more".',
                "url":      url,
            })


def _check_placeholder_as_label(soup, url, findings):
    """Flag inputs that use placeholder as their only label."""
    for inp in soup.find_all("input"):
        input_type = inp.get("type", "text").lower()
        if input_type in PLACEHOLDER_EXEMPT:
            continue
        if not inp.get("placeholder"):
            continue
        # If it has a real label via any method, skip it.
        if inp.get("aria-label") or inp.get("aria-labelledby"):
            continue
        if inp.find_parent("label"):
            continue
        input_id = inp.get("id")
        if input_id and soup.find("label", attrs={"for": input_id}):
            continue
        findings.append({
            "check":    METADATA["name"],
            "wcag":     "1.3.1",
            "level":    "A",
            "severity": config.SEVERITY_HIGH,
            "message":  f'<input type="{input_type}"> uses placeholder as its only label — '
                        f'placeholder text disappears on input and is not a substitute for a label. '
                        f'name="{inp.get("name", "[no name]")}"',
            "element":  str(inp),
            "fix_hint": "Add a visible <label> element or aria-label. "
                        "Placeholder text may be retained as a hint but must not "
                        "replace the label.",
            "url":      url,
        })


def _check_onclick_non_interactive(soup, url, findings):
    """Flag onclick handlers on non-interactive elements."""
    interactive = {"a", "button", "input", "select", "textarea", "details", "summary"}
    for el in soup.find_all(attrs={"onclick": True}):
        if el.name in interactive:
            continue
        findings.append({
            "check":    METADATA["name"],
            "wcag":     "4.1.2",
            "level":    "A",
            "severity": config.SEVERITY_HIGH,
            "message":  f'<{el.name}> has an onclick handler but is not a native '
                        f'interactive element — keyboard users cannot activate it. '
                        f'id="{el.get("id", "[no id]")}"',
            "element":  str(el)[:120],
            "fix_hint": "Replace the <{tag}> with a <button> element, or add "
                        'role="button" tabindex="0" and keyboard event handlers '
                        "(keydown Enter/Space) if a div/span is required.".format(
                            tag=el.name),
            "url":      url,
        })


def _check_table_headers(soup, url, findings):
    """Flag tables that have no <th> elements."""
    for table in soup.find_all("table"):
        # Skip tables marked as layout tables.
        role = table.get("role", "").lower()
        if role in ("presentation", "none"):
            continue
        if not table.find("th"):
            findings.append({
                "check":    METADATA["name"],
                "wcag":     "1.3.1",
                "level":    "A",
                "severity": config.SEVERITY_HIGH,
                "message":  "<table> has no <th> header cells — screen readers "
                            "cannot identify column or row headers.",
                "element":  str(table)[:120],
                "fix_hint": "Add <th scope='col'> for column headers and "
                            "<th scope='row'> for row headers. "
                            "If the table is used for layout only, add role='presentation'.",
                "url":      url,
            })


def _check_blank_target(soup, url, findings):
    """Flag links that open in a new tab without warning the user."""
    for link in soup.find_all("a", href=True, target="_blank"):
        text  = link.get_text(strip=True).lower()
        aria  = link.get("aria-label", "").lower()
        label = text + " " + aria
        # Accept if the label already warns about new tab/window.
        if any(w in label for w in ["new tab", "new window", "opens in"]):
            continue
        findings.append({
            "check":    METADATA["name"],
            "wcag":     "3.2.2",
            "level":    "A",
            "severity": config.SEVERITY_LOW,
            "message":  f'<a target="_blank"> opens a new tab without warning the user. '
                        f'text="{link.get_text(strip=True)}", '
                        f'href="{link.get("href", "")}"',
            "element":  str(link),
            "fix_hint": 'Add "(opens in new tab)" to the link text or aria-label. '
                        "Also add rel='noreferrer noopener' for security.",
            "url":      url,
        })


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Run all accessibility pattern checks.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: All findings across all pattern checks.
    """

    masLog(f"Running check: {METADATA['name']}")

    findings = []

    _check_generic_links(soup, url, findings)
    _check_placeholder_as_label(soup, url, findings)
    _check_onclick_non_interactive(soup, url, findings)
    _check_table_headers(soup, url, findings)
    _check_blank_target(soup, url, findings)

    if findings:
        masLog(f"{METADATA['name']} check: {len(findings)} pattern(s) found",
               level="warning")
    else:
        masLog(f"{METADATA['name']} check: passed")

    return findings