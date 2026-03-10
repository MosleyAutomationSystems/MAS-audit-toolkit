# checks/duplicate_ids.py
# Check 12: Elements with duplicate id attributes.
# WCAG 2.1 Success Criterion 4.1.1 — Parsing (Level A)
# Every id attribute must be unique within a document.
# Duplicate ids break aria-labelledby, aria-describedby, and
# label for= associations — assistive technologies will bind to
# the wrong element or fail silently.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "Duplicate ID",
    "wcag":     "4.1.1",
    "level":    "A",
    "severity": config.SEVERITY_CRITICAL,
    "fix_hint": "Every id attribute must be unique within the page. "
                "Rename duplicate ids so each value appears exactly once.",
}


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Find all elements whose id attribute value appears more than once.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding per duplicate id value, or empty list if none found.
    """

    masLog(f"Running check: {METADATA['name']}")

    # Collect every id value in the document, preserving the element.
    # We build a dict mapping id value → list of elements that carry it.
    id_map: dict[str, list] = {}
    for el in soup.find_all(attrs={"id": True}):
        id_val = el.get("id", "").strip()
        if not id_val:
            continue
        id_map.setdefault(id_val, []).append(el)

    masLog(f"Found {len(id_map)} unique id value(s) across the document")

    findings = []

    for id_val, elements in id_map.items():
        if len(elements) < 2:
            continue

        # Report once per duplicate id value, noting how many times it appears.
        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  f'id="{id_val}" appears {len(elements)} times — '
                        f"ids must be unique. "
                        f"First occurrence: <{elements[0].name}>.",
            "element":  str(elements[0]),
            "fix_hint": METADATA["fix_hint"],
            "url":      url,
        })

    if findings:
        masLog(f"{METADATA['name']} check: {len(findings)} duplicate id(s) found",
               level="warning")
    else:
        masLog(f"{METADATA['name']} check: passed")

    return findings