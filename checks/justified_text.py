# checks/justified_text.py
# Check 31: Justified text alignment in inline styles.
# WCAG 2.1 Success Criterion 1.4.8 — Visual Presentation (Level AAA)
#
# Text justified to both left and right margins creates uneven spacing
# between words — sometimes called "rivers of white space." These gaps
# create visual noise that disrupts reading for users with dyslexia,
# ADHD, and other cognitive or reading disabilities.
#
# Justified text is a typographic convention from print design that
# does not translate well to web content where line lengths vary by
# screen size and zoom level. On narrow screens or at high zoom,
# justified text can produce extreme word spacing that makes text
# nearly unreadable.
#
# WCAG 1.4.8 is Level AAA — it applies only when WCAG_REPORT_LEVEL
# is set to "AAA" in config.py. Under the default "AA" setting, this
# finding is separated into the AAA bucket and excluded from the main
# report and risk score.
#
# This check inspects inline styles only. External CSS text-align:justify
# rules are common in print stylesheets and require manual review.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "Justified Text Detection",
    "wcag":     "1.4.8",
    "level":    "AAA",
    "severity": config.SEVERITY_LOW,
    "fix_hint": "Replace text-align:justify with text-align:left (or start) "
                "for body text. Left-aligned text produces consistent word spacing "
                "that is easier to read for users with dyslexia, ADHD, and other "
                "reading disabilities. If justified text is required for design "
                "reasons, limit it to headings or short text blocks — never use "
                "it for paragraphs of body content.",
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
    Check elements with inline text-align:justify styles.

    Inspects inline styles only. External CSS requires manual review.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding per element with inline text-align:justify.
    """

    masLog(f"Running check: {METADATA['name']}")

    findings = []

    for element in soup.find_all(style=True):
        style_attr = element.get("style", "").strip()
        if not style_attr:
            continue

        props = _parse_inline_style(style_attr)
        text_align = props.get("text-align", "")

        if text_align != "justify":
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
            f"{METADATA['name']} check: <{element.name}> {el_ref} has text-align:justify",
            level="warning"
        )

        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  f"<{element.name}> has inline text-align:justify. "
                        f"Justified text creates uneven word spacing that disrupts "
                        f"reading for users with dyslexia and cognitive disabilities. "
                        f"{el_ref}. "
                        f"Note: this check inspects inline styles only.",
            "element":  str(element)[:120],
            "fix_hint": METADATA["fix_hint"],
            "line":   getattr(element, 'sourceline', None),
            "parent": "",
            "url":      url,
        })

    if not findings:
        masLog(f"{METADATA['name']} check: passed — no inline text-align:justify detected")

    return findings

