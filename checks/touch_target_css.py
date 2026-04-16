# checks/touch_target_css.py
# Check 17: Touch target size — CSS pointer:coarse media query check.
# WCAG 2.1 Success Criterion 2.5.5 — Target Size (Level AA)
# WCAG 2.2 Success Criterion 2.5.8 — Target Size Minimum (Level AA)
# Mosley Standard Category 5 — Motor Impairment
#
# Interactive elements must meet a minimum touch target size on coarse
# pointer devices (touchscreens). Small targets create barriers for users
# with motor impairments, tremors, or reduced precision.
#
# This check inspects inline styles and detects common small-target patterns.
# It cannot evaluate external CSS files — findings are flagged as indicators,
# not definitive failures. External CSS auditing requires a browser runtime.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "Touch Target CSS Check",
    "wcag":     "2.5.5",
    "level":    "AA",
    "severity": config.SEVERITY_MEDIUM,
    "fix_hint": "Ensure all interactive elements meet a 44x44px minimum touch "
                "target size on coarse pointer devices. Use the CSS pointer:coarse "
                "media query: @media (pointer: coarse) { button, a, input, select, "
                "textarea { min-height: 44px; min-width: 44px; } }. "
                "For the Tkinter desktop GUI, enable the Large Targets toggle in "
                "Settings to scale interactive elements to 48px minimum height.",
}

# Interactive element tags that must meet minimum target size.
INTERACTIVE_TAGS = {"a", "button", "input", "select", "textarea", "label"}

# Inline style properties that explicitly set small dimensions.
# These are the most common patterns that produce undersized targets.
SMALL_SIZE_PROPERTIES = {
    "width", "height", "min-width", "min-height",
    "max-width", "max-height",
}

# Pixel threshold below which a declared size is flagged as potentially too small.
# 44px is the WCAG 2.5.5 / Mosley Standard minimum.
# We flag anything explicitly set below this value.
MIN_TARGET_PX = config.MIN_TOUCH_TARGET  # 44 — from config.py, not hardcoded


def _parse_inline_style(style_str: str) -> dict:
    """
    Parse an inline style string into a property-value dict.

    Example: "width: 20px; height: 30px" → {"width": "20px", "height": "30px"}

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


def _extract_px_value(value: str) -> float | None:
    """
    Extract a numeric pixel value from a CSS value string.

    Returns the float value if the unit is px, or None if not px or unparseable.

    Parameters:
        value (str): CSS value string, e.g. "20px", "2rem", "auto".

    Returns:
        float | None: Pixel value, or None if not a px unit.
    """
    value = value.strip().lower()
    if value.endswith("px"):
        try:
            return float(value[:-2])
        except ValueError:
            return None
    return None


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Check interactive elements for inline styles that set explicitly small
    touch target dimensions below the 44px WCAG minimum.

    Scope limitation: This check only inspects inline styles. External
    stylesheets cannot be evaluated without a browser runtime. Findings
    are risk indicators — manual verification is required.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding per element with a flagged undersized inline style.
    """

    masLog(f"Running check: {METADATA['name']}")

    findings = []

    for tag in INTERACTIVE_TAGS:
        elements = soup.find_all(tag)
        for element in elements:
            style_attr = element.get("style", "")
            if not style_attr.strip():
                continue

            props = _parse_inline_style(style_attr)

            for prop in SMALL_SIZE_PROPERTIES:
                if prop not in props:
                    continue

                px_val = _extract_px_value(props[prop])
                if px_val is None:
                    continue

                if px_val < MIN_TARGET_PX:
                    # Build a readable element identifier for the finding message.
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
                        f"{METADATA['name']} check: <{tag}> {el_ref} "
                        f"has {prop}:{props[prop]} — below {MIN_TARGET_PX}px minimum",
                        level="warning"
                    )

                    findings.append({
                        "check":    METADATA["name"],
                        "wcag":     METADATA["wcag"],
                        "level":    METADATA["level"],
                        "severity": METADATA["severity"],
                        "message":  f"<{tag}> has inline {prop}:{props[prop]} — "
                                    f"below the {MIN_TARGET_PX}px minimum touch target size. "
                                    f"Small targets create barriers for users with motor "
                                    f"impairments or tremors. {el_ref}. "
                                    f"Note: this check inspects inline styles only — "
                                    f"external CSS requires manual verification.",
                        "element":  str(element)[:120],
                        "fix_hint": METADATA["fix_hint"],
                        "line":   getattr(element, 'sourceline', None),
                        "parent": "",
                        "url":      url,
                    })

    if not findings:
        masLog(f"{METADATA['name']} check: passed — no undersized inline targets detected")

    return findings

