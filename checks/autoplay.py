# checks/autoplay.py
# Check 9: Audio or video elements with autoplay enabled.
# WCAG 2.1 Success Criterion 1.4.2 — Audio Control (Level A)
# Media that plays automatically interferes with screen readers because
# the audio competes with the screen reader's voice output.
# Users must be able to pause, stop, or mute autoplay media.

from bs4 import BeautifulSoup
from utils.logger import masLog

def check_autoplay(soup: BeautifulSoup) -> list:
    """
    Find all <video> and <audio> elements with the autoplay attribute.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.

    Returns:
        list: A list of finding dictionaries for each autoplay element.
    """

    masLog("Running check: autoplay on <video> and <audio> elements")

    findings = []

    # Find all media elements that carry the autoplay attribute.
    # autoplay is a boolean attribute — its presence alone enables it.
    # The value does not matter: autoplay="" and autoplay="autoplay" both fire.
    media = soup.find_all(["video", "audio"], attrs={"autoplay": True})

    masLog(f"Found {len(media)} autoplay media element(s)")

    for el in media:
        tag = el.name
        src = el.get("src", "")

        # If no src on the element itself, check the first <source> child.
        # <video><source src="..."></video> is the common pattern.
        if not src:
            source_tag = el.find("source")
            src = source_tag.get("src", "[no src]") if source_tag else "[no src]"

        # Check whether a visible pause/stop control exists.
        # The presence of controls= is not a full fix but significantly
        # reduces the barrier — we note it in the message.
        has_controls = el.has_attr("controls")
        controls_note = (
            "controls attribute present but autoplay should still be removed"
            if has_controls else
            "no controls attribute — user cannot pause or stop playback"
        )

        findings.append({
            "check":    "Autoplay Media",
            "wcag":     "1.4.2",
            "level":    "A",
            "severity": "error",
            "message":  (
                f'<{tag}> has autoplay enabled — {controls_note}. '
                f'src="{src}"'
            )
        })

    if findings:
        masLog(f"Autoplay check: {len(findings)} issue(s) found", level="warning")
    else:
        masLog("Autoplay check: passed — no autoplay media found")

    return findings