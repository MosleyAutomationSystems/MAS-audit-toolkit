# checks/background_audio.py
# Check 46: Background audio playing beyond 3 seconds without pause control.
# WCAG 2.1 Success Criterion 1.4.2 — Audio Control (Level A)
#
# WCAG 1.4.2 states that if audio plays automatically for more than 3 seconds,
# the user must be able to pause, stop, or control the volume independently
# of the system volume. This check flags audio elements that:
#
#   1. Have autoplay enabled
#   2. Lack a controls attribute (no built-in pause/stop UI)
#   3. Have no mute button or visible pause mechanism detectable in HTML
#
# This is distinct from check #8 (autoplay.py) which flags all autoplay,
# and check #45 (muted_autoplay.py) which distinguishes muted vs unmuted.
# This check specifically targets the WCAG 1.4.2 "3 second" threshold
# and flags the absence of any accessible pause mechanism.
#
# Static HTML analysis cannot determine audio duration — this check flags
# patterns that indicate background audio is intended (autoplay without
# controls), which is a strong indicator of a 1.4.2 violation.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "Background Audio Check",
    "wcag":     "1.4.2",
    "level":    "A",
    "severity": config.SEVERITY_HIGH,
    "fix_hint": "Add the controls attribute to all <audio> elements to provide "
                "a built-in pause/stop/volume interface: <audio controls autoplay>. "
                "Better: remove autoplay entirely and let users initiate playback. "
                "If background audio is essential, provide a clearly labeled, "
                "keyboard-accessible pause button adjacent to the audio element. "
                "WCAG 1.4.2 requires that audio playing automatically for more than "
                "3 seconds can be paused, stopped, or its volume controlled "
                "independently of the system volume.",
}

# ARIA roles and attributes that indicate a pause/stop mechanism is present.
PAUSE_INDICATORS = {
    "aria-label": ["pause", "stop", "mute", "silence", "audio control"],
    "role":       ["button"],
}


def _has_nearby_pause_control(element) -> bool:
    """
    Check whether a pause/stop control exists near the audio element.

    Looks for buttons with pause-related aria-labels in the same parent
    container as the audio element.

    Parameters:
        element: A BeautifulSoup audio element.

    Returns:
        bool: True if a likely pause control is found nearby.
    """
    parent = element.parent
    if parent is None:
        return False

    for btn in parent.find_all(["button", "a", "input"], recursive=False):
        aria_label = btn.get("aria-label", "").lower()
        btn_text   = btn.get_text(strip=True).lower()
        combined   = aria_label + " " + btn_text
        if any(word in combined for word in ["pause", "stop", "mute", "silence"]):
            return True

    return False


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Flag audio elements with autoplay and no accessible pause mechanism.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding per audio element with autoplay and no pause control.
    """

    masLog(f"Running check: {METADATA['name']}")

    findings = []

    for element in soup.find_all("audio"):
        # Only flag elements with autoplay.
        if "autoplay" not in element.attrs:
            continue

        # Pass if the browser controls are present — user can pause.
        if "controls" in element.attrs:
            continue

        # Pass if a nearby pause control is found.
        if _has_nearby_pause_control(element):
            continue

        src    = element.get("src", "[no src]")[:80]
        el_id  = element.get("id", "")
        el_ref = f'id="{el_id}"' if el_id else f'src="{src}"'

        is_muted = element.get("muted") is not None
        mute_note = " Element is muted so audio impact is low, but a pause mechanism is still required." if is_muted else ""

        masLog(
            f"{METADATA['name']} check: <audio> {el_ref} has autoplay "
            f"with no controls or pause mechanism",
            level="warning"
        )

        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  f"<audio> has autoplay enabled with no controls attribute "
                        f"and no detectable pause mechanism. If this audio plays "
                        f"for more than 3 seconds, WCAG 1.4.2 requires a way to "
                        f"pause, stop, or control volume independently.{mute_note} "
                        f"{el_ref}",
            "element":  str(element)[:120],
            "fix_hint": METADATA["fix_hint"],
            "line":   getattr(element, 'sourceline', None),
            "parent": "",
            "url":      url,
        })

    if not findings:
        masLog(f"{METADATA['name']} check: passed — no uncontrolled background audio detected")

    return findings