# checks/outline_none.py
# Check 23: CSS outline:none or outline:0 removing focus indicators.
# WCAG 2.1 Success Criterion 2.4.7 — Focus Visible (Level AA)
#
# The CSS property outline:none (or outline:0) removes the browser's
# default focus ring from interactive elements. This focus ring is the
# primary visual indicator that tells keyboard users which element
# currently has focus. Without it, keyboard-only users and low-vision
# users who rely on keyboard navigation cannot tell where they are on
# the page.
#
# This check inspects inline styles only. The most common violation is
# a blanket rule like *:focus { outline: none } in external CSS —
# that pattern requires manual inspection of CSS files and cannot be
# detected here. Findings are risk indicators, not definitive failures.
#
# A finding does NOT fire if the element also has a visible replacement
# focus indicator via other inline style properties (box-shadow, border,
# background-color change). However, inline replacements are rare —
# external CSS replacements cannot be verified here.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "outline:none Detection",
    "wcag":     "2.4.7",
    "level":    "AA",
    "severity": config.SEVERITY_HIGH,
    "fix_hint": "Never use outline:none or outline:0 on interactive elements "
                "without providing a visible focus replacement. Instead, style "
                "the focus indicator: a:focus { outline: 2px solid #4ea8de; "
                "outline-offset: 2px; }. If a custom focus style is needed, "
                "ensure it has at least 3:1 contrast ratio against adjacent colors "
                "and is at least 2px wide (WCAG 2.4.11). "
                "Note: this check inspects inline styles only — "
                "check external CSS files for blanket outline:none rules.",
}

# Inline style values that remove the focus outline.
OUTLINE_NONE_VALUES = {"none", "0", "0px"}

# Inline style properties that may serve as visible focus replacements.
# If any of these are present alongside outline:none, suppress the finding.
REPLACEMENT_INDICATORS = {"box-shadow", "border", "background-color", "background"}


def _parse_inline_style(style_str: str) -> dict:
    """
    Parse an inline style string into a property-value dict.

    Parameters:
        style_str (str): Raw value of the style attribute.

    Returns:
        dict: Lowercased property names mapped to lowercased values.
    """
    props = {}
    for declaration in style_str.split(";"):
        declaration = declaration.strip()
        if ":" in declaration:
            prop, _, val = declaration.partition(":")
            props[prop.strip().lower()] = val.strip().lower()
    return props


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Check interactive elements for inline outline:none or outline:0
    without a visible focus replacement.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding per element with outline removed and no replacement.
    """

    masLog(f"Running check: {METADATA['name']}")

    findings = []

    # Interactive elements where focus visibility is required.
    interactive_tags = {"a", "button", "input", "select", "textarea"}

    for tag in interactive_tags:
        elements = soup.find_all(tag)
        for element in elements:
            style_attr = element.get("style", "").strip()
            if not style_attr:
                continue

            props = _parse_inline_style(style_attr)

            outline_val = props.get("outline", "")
            if outline_val not in OUTLINE_NONE_VALUES:
                continue

            # Check for inline replacement focus indicators.
            has_replacement = any(
                prop in props for prop in REPLACEMENT_INDICATORS
            )
            if has_replacement:
                continue

            # Build element identifier.
            el_id    = element.get("id", "")
            el_class = " ".join(element.get("class", []))
            el_text  = element.get_text(strip=True)[:30]
            el_ref   = (
                f'id="{el_id}"' if el_id
                else f'class="{el_class}"' if el_class
                else f'text="{el_text}"' if el_text
                else "[no identifier]"
            )

            masLog(
                f"{METADATA['name']} check: <{tag}> {el_ref} has outline:{outline_val}",
                level="warning"
            )

            findings.append({
                "check":    METADATA["name"],
                "wcag":     METADATA["wcag"],
                "level":    METADATA["level"],
                "severity": METADATA["severity"],
                "message":  f"<{tag}> has inline outline:{outline_val} with no visible "
                            f"focus replacement — keyboard users cannot see which element "
                            f"has focus. {el_ref}. "
                            f"Note: this check inspects inline styles only — "
                            f"external CSS outline:none rules require manual review.",
                "element":  str(element)[:120],
                "fix_hint": METADATA["fix_hint"],
                "line":   getattr(element, 'sourceline', None),
                "parent": "",
                "url":      url,
            })

    if not findings:
        masLog(f"{METADATA['name']} check: passed — no inline outline:none detected on interactive elements")

    return findings

