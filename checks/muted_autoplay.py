# checks/muted_autoplay.py
# Check 45: Muted autoplay extension — unmuted autoplay flagged separately.
# WCAG 2.1 Success Criterion 1.4.2 — Audio Control (Level A)
#
# Check 8 (autoplay.py) flags all autoplay media as HIGH severity.
# This check extends that by distinguishing between:
#
#   - Unmuted autoplay (no muted attribute): CRITICAL
#     Audio begins playing automatically with no user control.
#     This is the most disruptive pattern — screen reader users may be
#     unable to hear their screen reader over the autoplaying audio.
#     WCAG 1.4.2 specifically addresses audio that plays automatically.
#
#   - Muted autoplay (muted attribute present): LOW
#     Visual autoplay only. No audio disruption. Still flagged as a
#     best-practice issue since animation can distract users with
#     cognitive disabilities, but the accessibility risk is lower.
#
# This check runs independently of autoplay.py. Both checks may fire
# on the same element. The distinction in severity helps clients
# prioritize which autoplay issues to address first.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "Muted Autoplay Extension",
    "wcag":     "1.4.2",
    "level":    "A",
    "severity": config.SEVERITY_CRITICAL,  # Default for unmuted; overridden per finding.
    "fix_hint": "For unmuted autoplay: remove the autoplay attribute entirely, or add "
                "the muted attribute and provide a visible play button so users can "
                "choose to start audio. For muted autoplay: consider adding "
                "prefers-reduced-motion media query support to pause animation for "
                "users who have requested reduced motion in their OS settings. "
                "WCAG 1.4.2 requires that audio playing for more than 3 seconds "
                "can be paused, stopped, or its volume controlled independently.",
}


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Distinguish between unmuted autoplay (CRITICAL) and muted autoplay (LOW).

    Flags <video> and <audio> elements with autoplay.
    Severity is assigned per element based on the muted attribute.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding per autoplay media element, severity by muted status.
    """

    masLog(f"Running check: {METADATA['name']}")

    findings = []

    for tag_name in ("video", "audio"):
        for element in soup.find_all(tag_name):
            if element.get("autoplay") is None:
                continue

            is_muted  = element.get("muted") is not None
            has_controls = element.get("controls") is not None
            src       = element.get("src", "[no src]")[:80]
            el_id     = element.get("id", "")
            el_ref    = f'id="{el_id}"' if el_id else f'src="{src}"'

            if is_muted:
                severity = config.SEVERITY_LOW
                muted_note = "muted"
                issue = (
                    f"<{tag_name}> has autoplay with muted attribute — "
                    f"visual autoplay only, no audio disruption. "
                    f"Consider supporting prefers-reduced-motion for users "
                    f"sensitive to animation. {el_ref}"
                )
            else:
                severity = config.SEVERITY_CRITICAL
                muted_note = "unmuted"
                controls_note = " No controls attribute — user cannot pause or stop." if not has_controls else ""
                issue = (
                    f"<{tag_name}> has unmuted autoplay — audio begins "
                    f"playing automatically without user consent.{controls_note} "
                    f"Screen reader users may be unable to hear their assistive "
                    f"technology over the autoplaying audio. {el_ref}"
                )

            masLog(
                f"{METADATA['name']} check: <{tag_name}> {el_ref} "
                f"has {muted_note} autoplay",
                level="warning"
            )

            findings.append({
                "check":    METADATA["name"],
                "wcag":     METADATA["wcag"],
                "level":    METADATA["level"],
                "severity": severity,
                "message":  issue,
                "element":  str(element)[:120],
                "fix_hint": METADATA["fix_hint"],
                "line":   getattr(element, 'sourceline', None),
                "parent": "",
                "url":      url,
            })

    if not findings:
        masLog(f"{METADATA['name']} check: passed — no autoplay media detected")

    return findings