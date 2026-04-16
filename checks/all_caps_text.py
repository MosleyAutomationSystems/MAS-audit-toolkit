# checks/all_caps_text.py
# Check 32: All-caps text via text-transform:uppercase in inline styles.
# WCAG 2.1 Success Criterion 1.4.8 — Visual Presentation (Level AAA)
#
# Text rendered in all capital letters via CSS text-transform:uppercase
# creates reading difficulties for users with dyslexia. All-caps text
# removes the distinctive shape (ascenders and descenders) of lowercase
# letters that readers use to recognize words. Users with dyslexia rely
# heavily on word shape for recognition — all-caps text forces slower,
# letter-by-letter decoding.
#
# Additionally, screen readers may announce all-caps text as acronyms,
# reading each letter individually (e.g. "HELLO" read as "H-E-L-L-O")
# depending on the screen reader and its settings. This creates an
# incomprehensible audio experience for blind users.
#
# WCAG 1.4.8 is Level AAA — this finding only appears when
# WCAG_REPORT_LEVEL is set to "AAA" in config.py.
#
# This check inspects inline styles only. External CSS text-transform
# rules require manual review.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "All-Caps Text Detection",
    "wcag":     "1.4.8",
    "level":    "AAA",
    "severity": config.SEVERITY_LOW,
    "fix_hint": "Avoid text-transform:uppercase for body text and headings. "
                "If all-caps styling is required for design purposes, type the "
                "text in mixed case in the HTML and apply the CSS transformation "
                "only to short labels or UI elements (not paragraphs). "
                "For screen reader compatibility, ensure the underlying HTML "
                "text is in mixed case — screen readers read the DOM text, "
                "not the CSS-transformed visual output. "
                "Example: <button>SUBMIT</button> reads as 'S-U-B-M-I-T' on some "
                "screen readers. Use <button>Submit</button> with CSS if needed.",
}


def _parse_inline_style(style_str: str) -> dict:
    """Parse inline style string to property-value dict."""
    props = {}
    for declaration in style_str.split(";"):
        declaration = declaration.strip()
        if ":" in declaration:
            prop, _, val = declaration.partition(":")
            props[prop.strip().lower()] = val.strip().lower()
    return props


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Check elements with inline text-transform:uppercase styles.

    Inspects inline styles only. External CSS requires manual review.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding per element with inline text-transform:uppercase.
    """

    masLog(f"Running check: {METADATA['name']}")

    findings = []

    for element in soup.find_all(style=True):
        style_attr = element.get("style", "").strip()
        if not style_attr:
            continue

        props = _parse_inline_style(style_attr)
        text_transform = props.get("text-transform", "")

        if text_transform != "uppercase":
            continue

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
            f"{METADATA['name']} check: <{element.name}> {el_ref} has text-transform:uppercase",
            level="warning"
        )

        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  f"<{element.name}> has inline text-transform:uppercase. "
                        f"All-caps text removes word shape cues that users with dyslexia "
                        f"rely on for reading. Some screen readers may also read "
                        f"all-caps text letter-by-letter as an acronym. "
                        f"{el_ref}. "
                        f"Note: this check inspects inline styles only.",
            "element":  str(element)[:120],
            "fix_hint": METADATA["fix_hint"],
            "line":   getattr(element, 'sourceline', None),
            "parent": "",
            "url":      url,
        })

    if not findings:
        masLog(f"{METADATA['name']} check: passed — no inline text-transform:uppercase detected")

    return findings

