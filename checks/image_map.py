# checks/image_map.py
# Check 39: Image map area elements missing alt text.
# WCAG 2.1 Success Criterion 1.1.1 — Non-text Content (Level A)
#
# Image maps use <map> and <area> elements to create clickable regions
# on an image. Each <area> element is essentially a link — it has an
# href and navigates users to a destination. Like all links, each area
# must have an accessible name so screen reader users know where it goes.
#
# The accessible name for an <area> element comes from its alt attribute.
# Without alt text, screen readers announce the area as an unlabeled link,
# giving users no information about the destination.
#
# Two cases are flagged:
#   1. <area> missing the alt attribute entirely
#   2. <area> with an empty alt attribute (alt="") on a non-decorative area
#
# Note: <area> elements with shape="default" that serve as a fallback
# for the entire image should still have descriptive alt text.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "Image Map Check",
    "wcag":     "1.1.1",
    "level":    "A",
    "severity": config.SEVERITY_HIGH,
    "fix_hint": "Add a descriptive alt attribute to every <area> element in an "
                "image map. The alt text should describe the link destination, "
                "not the visual appearance of the region. Example: "
                "<area shape=\"rect\" coords=\"0,0,100,100\" href=\"/about\" "
                "alt=\"About our company\">. "
                "If an area is purely decorative and has no href, use alt=\"\" "
                "to mark it as decorative.",
}


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Check all <area> elements for descriptive alt text.

    Flags areas that are missing the alt attribute or have empty alt
    on an element that has an href (i.e. is a functional link).

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding per <area> missing a valid alt attribute.
    """

    masLog(f"Running check: {METADATA['name']}")

    areas = soup.find_all("area")

    if not areas:
        masLog(f"{METADATA['name']} check: passed — no <area> elements found")
        return []

    findings = []

    for area in areas:
        alt  = area.get("alt", None)
        href = area.get("href", "")

        # Area with no href is non-interactive — decorative, skip.
        if not href and alt is not None and alt.strip() == "":
            continue

        if alt is None:
            issue = "missing alt attribute"
        elif not alt.strip() and href:
            issue = "empty alt attribute on a linked area"
        else:
            continue

        shape  = area.get("shape", "rect")
        coords = area.get("coords", "[no coords]")[:40]
        el_ref = f'shape="{shape}" coords="{coords}"'

        masLog(
            f"{METADATA['name']} check: <area> {el_ref} has {issue}",
            level="warning"
        )

        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  f"<area> element has {issue} — screen readers will "
                        f"announce this as an unlabeled link with no destination context. "
                        f"{el_ref}, href=\"{href[:60]}\"",
            "element":  str(area)[:120],
            "fix_hint": METADATA["fix_hint"],
            "line":   getattr(area, 'sourceline', None),
            "parent": "",
            "url":      url,
        })

    if not findings:
        masLog(f"{METADATA['name']} check: passed — all <area> elements have valid alt text")

    return findings

