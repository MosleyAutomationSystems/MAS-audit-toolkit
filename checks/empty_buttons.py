# checks/empty_buttons.py
# Check 8: Button elements with no accessible name.
# WCAG 2.1 Success Criterion 4.1.2 — Name, Role, Value (Level A)
# A screen reader announces a button by its accessible name.
# A button with no name is announced as "button" with no context —
# the user cannot determine what it does without clicking it blindly.

from bs4 import BeautifulSoup
from utils.logger import masLog
import config
METADATA = {
    "name":     "Button Name Detection",
    "wcag":     "4.1.2",
    "level":    "A",
    "severity": config.SEVERITY_CRITICAL,
    "fix_hint": "Add an aria-label attribute, visible text content, or a child <img> with alt text to every button element.",
}

def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Find all <button> elements that have no accessible name.

    An accessible name is present if ANY of these exist:
    1. Non-empty visible text content inside the element
    2. An aria-label attribute with non-empty value
    3. An aria-labelledby attribute
    4. A child <img> with a non-empty alt attribute
    5. A value attribute (for <input type="button"> and <input type="submit">)

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.

    Returns:
        list: A list of finding dictionaries for each nameless button.
    """

    masLog(f"Running check: {METADATA['name']}")

    findings = []

    # Find all <button> elements and button-type <input> elements.
    # Both are interactive controls that require an accessible name.
    buttons = soup.find_all("button")
    input_buttons = soup.find_all("input", attrs={
        "type": lambda t: t and t.lower() in ("button", "submit", "reset", "image")
    })

    all_buttons = buttons + input_buttons
    masLog(f"Found {len(all_buttons)} button element(s) to check")

    for btn in all_buttons:

        # Check 1: aria-label
        if btn.get("aria-label", "").strip():
            continue

        # Check 2: aria-labelledby
        if btn.get("aria-labelledby", "").strip():
            continue

        # Check 3: visible text content (for <button> elements)
        if btn.get_text(strip=True):
            continue

        # Check 4: child <img> with alt text (icon buttons)
        img = btn.find("img")
        if img and img.get("alt", "").strip():
            continue

        # Check 5: value attribute (for <input type="button"> etc.)
        if btn.get("value", "").strip():
            continue

        tag  = btn.name
        id_  = btn.get("id",   "[no id]")
        type_ = btn.get("type", "button")

        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  f'<{tag} type="{type_}"> has no accessible name — screen readers will announce "button" with no context. id="{id_}"',
            "element":  str(btn),
            "fix_hint": METADATA["fix_hint"],
            "line":   getattr(btn, 'sourceline', None),
            "parent": "",
            "url":      url,
        })

    if findings:
        masLog(f"Empty button check: {len(findings)} issue(s) found", level="warning")
    else:
        masLog("Empty button check: passed — all buttons have accessible names")

    return findings

