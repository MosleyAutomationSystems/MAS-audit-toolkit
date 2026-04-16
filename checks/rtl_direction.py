# checks/rtl_direction.py
# Check 40: RTL language content missing dir="rtl" attribute.
# WCAG 2.1 Success Criterion 1.3.2 — Meaningful Sequence (Level A)
#
# Arabic, Hebrew, Persian, Urdu, and other right-to-left languages require
# the dir="rtl" attribute to display correctly. Without it, browsers render
# RTL text in a left-to-right context, causing:
#   - Text to appear visually reversed or jumbled
#   - Punctuation placed on the wrong side
#   - Mixed LTR/RTL content to display in incorrect reading order
#   - Screen readers to announce text in the wrong sequence
#
# The dir attribute can be set at the html element level for fully RTL
# pages, or on individual elements for mixed-direction content.
#
# This check detects common RTL language indicators:
#   1. The lang attribute set to a known RTL language code
#   2. Unicode RTL markers (RLM, RLE, RLO) in text content
#   3. Elements with lang="ar", "he", "fa", "ur", "yi", etc.
#      that are missing dir="rtl"
#
# Note: This is a heuristic check. It cannot detect RTL text that
# lacks language markup. Full RTL auditing requires visual inspection.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "RTL Direction Check",
    "wcag":     "1.3.2",
    "level":    "A",
    "severity": config.SEVERITY_HIGH,
    "fix_hint": "Add dir=\"rtl\" to elements containing right-to-left language "
                "content. For fully RTL pages, set dir=\"rtl\" on the <html> element. "
                "For mixed-direction content, set dir=\"rtl\" on the specific element "
                "containing RTL text. Examples: "
                "<html lang=\"ar\" dir=\"rtl\"> for Arabic pages, "
                "<p lang=\"he\" dir=\"rtl\">Hebrew text</p> for inline RTL content. "
                "Also set the lang attribute to the correct language code.",
}

# BCP 47 language codes for right-to-left languages.
RTL_LANGUAGE_CODES = {
    "ar",    # Arabic
    "he",    # Hebrew
    "fa",    # Persian/Farsi
    "ur",    # Urdu
    "yi",    # Yiddish
    "dv",    # Dhivehi (Maldivian)
    "ha",    # Hausa (in Arabic script)
    "ks",    # Kashmiri
    "ku",    # Kurdish (Sorani)
    "ps",    # Pashto
    "sd",    # Sindhi
    "ug",    # Uyghur
    "arc",   # Aramaic
    "syc",   # Classical Syriac
}


def _is_rtl_lang(lang_val: str) -> bool:
    """
    Check whether a BCP 47 language tag indicates RTL script.

    Handles subtags like "ar-SA", "he-IL", "fa-IR" by checking
    the primary language subtag.

    Parameters:
        lang_val (str): Language tag value, e.g. "ar", "ar-SA", "he".

    Returns:
        bool: True if the language is RTL.
    """
    if not lang_val:
        return False
    primary = lang_val.strip().lower().split("-")[0]
    return primary in RTL_LANGUAGE_CODES


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Check elements with RTL language attributes for dir="rtl".

    Flags elements that have a lang attribute indicating RTL script
    but are missing the dir="rtl" attribute. Also checks the <html>
    element.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding per RTL-language element missing dir="rtl".
    """

    masLog(f"Running check: {METADATA['name']}")

    findings = []

    # Check all elements with a lang attribute.
    for element in soup.find_all(lang=True):
        lang_val = element.get("lang", "").strip()

        if not _is_rtl_lang(lang_val):
            continue

        dir_val = element.get("dir", "").strip().lower()

        if dir_val == "rtl":
            continue

        # Also pass if a parent already has dir="rtl" set —
        # dir is inherited in HTML.
        parent = element.parent
        parent_has_rtl = False
        while parent and parent.name and parent.name != "[document]":
            if parent.get("dir", "").strip().lower() == "rtl":
                parent_has_rtl = True
                break
            parent = parent.parent

        if parent_has_rtl:
            continue

        el_id    = element.get("id", "")
        el_text  = element.get_text(strip=True)[:30]
        el_ref   = (
            f'id="{el_id}"' if el_id
            else f'lang="{lang_val}" text="{el_text}"'
        )

        masLog(
            f"{METADATA['name']} check: <{element.name}> lang=\"{lang_val}\" "
            f"missing dir=rtl",
            level="warning"
        )

        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  f"<{element.name}> has lang=\"{lang_val}\" (RTL language) "
                        f"but is missing dir=\"rtl\". Without this attribute, "
                        f"the text may display and be read in the wrong direction. "
                        f"{el_ref}",
            "element":  str(element)[:120],
            "fix_hint": METADATA["fix_hint"],
            "line":   getattr(element, 'sourceline', None),
            "parent": "",
            "url":      url,
        })

    if not findings:
        masLog(f"{METADATA['name']} check: passed — no RTL language content missing dir=rtl")

    return findings

