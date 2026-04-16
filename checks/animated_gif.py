# checks/animated_gif.py
# Check 20: Animated GIF detection.
# WCAG 2.1 Success Criterion 2.3.1 — Three Flashes or Below Threshold (Level AA)
# WCAG 2.1 Success Criterion 2.2.2 — Pause, Stop, Hide (Level A)
#
# Animated GIFs that auto-play cannot be paused, stopped, or hidden by the user.
# They may flash at a rate that triggers photosensitive epilepsy seizures (2.3.1)
# or create distraction that prevents users with ADHD or cognitive disabilities
# from reading content (2.2.2).
#
# This check detects .gif files referenced in <img> src attributes and flags them
# as informational findings requiring manual verification. Static GIFs cannot be
# distinguished from animated ones without reading the binary file header —
# this check flags all GIFs for human review, noting that animated GIFs require
# a pause/stop mechanism or replacement with a static image or video element.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "Animated GIF Detection",
    "wcag":     "2.3.1",
    "level":    "AA",
    "severity": config.SEVERITY_LOW,
    "fix_hint": "Review all flagged GIF images to determine if they are animated. "
                "For animated GIFs: (1) Replace with a <video> element that has "
                "controls and does not autoplay, or (2) provide a pause/stop "
                "mechanism adjacent to the GIF, or (3) replace with a static image "
                "if animation is not essential. Animated GIFs that flash more than "
                "3 times per second may trigger photosensitive epilepsy seizures.",
}


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Detect <img> elements referencing .gif files and flag them for manual review.

    Cannot determine programmatically whether a GIF is animated without reading
    the binary file. All GIF references are flagged as LOW severity informational
    findings requiring human verification.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding per <img> element referencing a .gif file.
    """

    masLog(f"Running check: {METADATA['name']}")

    findings = []

    images = soup.find_all("img")

    for img in images:
        src = img.get("src", "").strip().lower()

        if not src.endswith(".gif"):
            continue

        # Build a readable identifier.
        alt    = img.get("alt", "[no alt]")
        img_id = img.get("id", "")
        el_ref = (
            f'id="{img_id}"' if img_id
            else f'alt="{alt[:40]}"' if alt and alt != "[no alt]"
            else f'src="{src[:60]}"'
        )

        masLog(
            f"{METADATA['name']} check: GIF detected — {el_ref}",
            level="warning"
        )

        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  f"GIF image detected — verify whether this is animated. "
                        f"Animated GIFs auto-play without a pause mechanism and may "
                        f"trigger photosensitive epilepsy or distract users with "
                        f"cognitive disabilities. Manual review required. {el_ref}. "
                        f'src="{src[:80]}"',
            "element":  str(img)[:120],
            "fix_hint": METADATA["fix_hint"],
            "line":   getattr(img, 'sourceline', None),
            "parent": "",
            "url":      url,
        })

    if not findings:
        masLog(f"{METADATA['name']} check: passed — no GIF images detected")

    return findings

