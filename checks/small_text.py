# checks/small_text.py
# Check 30: Inline text below minimum readable size.
# WCAG 2.1 Success Criterion 1.4.4 — Resize Text (Level AA)
# Mosley Standard — Category 2 (Low Vision)
#
# Text below 9pt (12px) is considered too small for comfortable reading
# by users with low vision, even when browser zoom is available. While
# WCAG 1.4.4 primarily addresses zoom functionality, the Mosley Standard
# sets 9pt/12px as the absolute minimum font size for all text.
#
# This check inspects inline styles only. External CSS font-size rules
# require a browser runtime to evaluate. Findings are risk indicators
# for inline style violations — a common pattern in legacy HTML emails,
# fine print disclosures, and CMS-generated content.
#
# Conversion reference:
#   12px = 9pt = 0.75rem (at default 16px root)
#   Any inline font-size below 12px is flagged.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "Small Text Detection",
    "wcag":     "1.4.4",
    "level":    "AA",
    "severity": config.SEVERITY_MEDIUM,
    "fix_hint": "Set a minimum font size of 12px (9pt) for all text. "
                "Remove or increase inline font-size declarations below 12px. "
                "In CSS: body { font-size: 1rem; } (16px default). "
                "Never use font-size below 12px for any content users need to read. "
                "If small text is used for decorative purposes only, ensure it "
                "carries no meaningful information and has aria-hidden=\"true\".",
}

# Minimum font size in pixels per Mosley Standard Category 2.
MIN_FONT_SIZE_PX = 12


def _parse_inline_style(style_str: str) -> dict:
    """Parse inline style string to property-value dict."""
    props = {}
    for declaration in style_str.split(";"):
        declaration = declaration.strip()
        if ":" in declaration:
            prop, _, val = declaration.partition(":")
            props[prop.strip().lower()] = val.strip().lower()
    return props


def _extract_font_size_px(value: str) -> float | None:
    """
    Convert a CSS font-size value to pixels where possible.

    Handles px and pt units. Returns None for relative units
    (em, rem, %) that cannot be resolved without a browser runtime.

    Parameters:
        value (str): CSS font-size value string.

    Returns:
        float | None: Pixel value, or None if not resolvable.
    """
    value = value.strip().lower()

    if value.endswith("px"):
        try:
            return float(value[:-2])
        except ValueError:
            return None

    if value.endswith("pt"):
        try:
            # 1pt = 1.333...px at 96dpi
            return float(value[:-2]) * (4 / 3)
        except ValueError:
            return None

    # em, rem, %, vw, etc. — cannot resolve without browser context.
    return None


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Check elements with inline font-size styles below the 12px minimum.

    Inspects inline styles only. External CSS requires manual review.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding per element with inline font-size below 12px.
    """

    masLog(f"Running check: {METADATA['name']}")

    findings = []

    for element in soup.find_all(style=True):
        style_attr = element.get("style", "").strip()
        if not style_attr:
            continue

        props = _parse_inline_style(style_attr)
        font_size_raw = props.get("font-size", "")
        if not font_size_raw:
            continue

        px_val = _extract_font_size_px(font_size_raw)
        if px_val is None:
            continue

        if px_val >= MIN_FONT_SIZE_PX:
            continue

        # Build element identifier.
        el_id    = element.get("id", "")
        el_class = " ".join(element.get("class", []))
        el_text  = element.get_text(strip=True)[:40]
        el_ref   = (
            f'id="{el_id}"' if el_id
            else f'class="{el_class}"' if el_class
            else f'text="{el_text}"' if el_text
            else "[no identifier]"
        )

        masLog(
            f"{METADATA['name']} check: <{element.name}> {el_ref} "
            f"has font-size:{font_size_raw} — below {MIN_FONT_SIZE_PX}px minimum",
            level="warning"
        )

        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  f"<{element.name}> has inline font-size:{font_size_raw} "
                        f"({px_val:.1f}px) — below the {MIN_FONT_SIZE_PX}px minimum. "
                        f"Text this small is difficult to read for low-vision users. "
                        f"{el_ref}. "
                        f"Note: this check inspects inline styles only.",
            "element":  str(element)[:120],
            "fix_hint": METADATA["fix_hint"],
            "line":   getattr(element, 'sourceline', None),
            "parent": "",
            "url":      url,
        })

    if not findings:
        masLog(f"{METADATA['name']} check: passed — no inline text below {MIN_FONT_SIZE_PX}px detected")

    return findings

