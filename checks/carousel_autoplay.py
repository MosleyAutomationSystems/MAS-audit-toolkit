# checks/carousel_autoplay.py
# Check 48: Auto-advancing carousels and sliders without pause mechanism.
# WCAG 2.1 Success Criterion 2.2.2 — Pause, Stop, Hide (Level AA)
#
# Carousels and sliders that auto-advance create barriers for users who:
#   - Need more time to read content before it changes (cognitive disabilities)
#   - Use keyboard navigation and lose their place when content shifts
#   - Have vestibular disorders triggered by motion (2.3.3 AAA)
#   - Use screen readers that announce content as it changes automatically
#
# WCAG 2.2.2 requires that auto-advancing content can be paused, stopped,
# or hidden by the user. A static display that does not auto-advance
# is the preferred accessible pattern.
#
# This check detects common carousel patterns through:
#   1. ARIA role="region" or role="group" with carousel-related labels
#   2. Elements with carousel/slider class name patterns
#   3. Data attributes commonly used by carousel libraries
#   4. Auto-advancing indicators (data-autoplay, data-interval, data-ride)
#
# Static HTML analysis cannot confirm whether JavaScript makes content
# auto-advance. This check flags patterns that strongly suggest carousels
# and checks for the presence of pause/stop controls.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "Carousel/Slider Autoplay",
    "wcag":     "2.2.2",
    "level":    "AA",
    "severity": config.SEVERITY_MEDIUM,
    "fix_hint": "Add a visible, keyboard-accessible pause/stop button to any "
                "auto-advancing carousel or slider. The pause control must be "
                "reachable before the moving content in the tab order. "
                "Better: disable auto-advance entirely and let users navigate "
                "slides manually. If auto-advance is required, ensure the carousel "
                "also pauses when keyboard focus enters the carousel region "
                "and resumes only when focus leaves.",
}

# Class name patterns that strongly suggest carousel/slider components.
CAROUSEL_CLASS_PATTERNS = [
    "carousel", "slider", "slideshow", "swiper", "splide",
    "slick", "glide", "flickity", "owl-carousel", "embla",
    "hero-slider", "banner-slider", "image-slider",
]

# Data attributes used by common carousel libraries to enable autoplay.
AUTOPLAY_DATA_ATTRS = [
    "data-autoplay", "data-auto-play", "data-interval",
    "data-ride", "data-slick", "data-swiper",
    "data-cycle", "data-delay",
]

# ARIA labels that suggest carousel regions.
CAROUSEL_ARIA_PATTERNS = [
    "carousel", "slider", "slideshow", "gallery", "banner",
]

# Class patterns that indicate a pause/stop control is present.
PAUSE_CLASS_PATTERNS = [
    "pause", "stop", "play-pause", "carousel-pause",
    "slider-pause", "autoplay-toggle",
]


def _has_carousel_classes(element) -> bool:
    """Check if element has carousel-related class names."""
    classes = " ".join(element.get("class", [])).lower()
    return any(pattern in classes for pattern in CAROUSEL_CLASS_PATTERNS)


def _has_autoplay_attribute(element) -> bool:
    """Check if element has autoplay-related data attributes."""
    for attr in AUTOPLAY_DATA_ATTRS:
        val = element.get(attr)
        if val is not None:
            # data-autoplay="false" or data-autoplay="0" means autoplay is off.
            if str(val).lower() in ("false", "0", "no"):
                continue
            return True
    return False


def _has_pause_control(element) -> bool:
    """
    Check whether a pause/stop control exists within the carousel element.
    """
    # Check for buttons with pause-related classes or aria-labels.
    for btn in element.find_all(["button", "a"]):
        btn_classes = " ".join(btn.get("class", [])).lower()
        aria_label  = btn.get("aria-label", "").lower()
        btn_text    = btn.get_text(strip=True).lower()
        combined    = btn_classes + " " + aria_label + " " + btn_text
        if any(pattern in combined for pattern in PAUSE_CLASS_PATTERNS):
            return True
        if any(word in combined for word in ["pause", "stop", "play/pause"]):
            return True
    return False


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Detect carousel/slider patterns and flag those without pause controls.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding per carousel without a detectable pause mechanism.
    """

    masLog(f"Running check: {METADATA['name']}")

    findings = []
    reported = set()

    # Pattern 1: Elements with carousel class names.
    for element in soup.find_all(True):
        if id(element) in reported:
            continue
        if not _has_carousel_classes(element):
            continue

         # Skip child elements whose parent is already a carousel container.
        parent = element.parent
        if parent and _has_carousel_classes(parent):
            continue

        # Only flag if autoplay attributes are present OR no pause control found.
        has_autoplay = _has_autoplay_attribute(element)
        has_pause    = _has_pause_control(element)

        if has_pause:
            continue

        reported.add(id(element))

        el_id    = element.get("id", "")
        el_class = " ".join(element.get("class", []))[:60]
        el_ref   = f'id="{el_id}"' if el_id else f'class="{el_class}"'

        autoplay_note = " Autoplay attribute detected." if has_autoplay else \
                        " No autoplay attribute detected in HTML — verify via JavaScript."

        masLog(
            f"{METADATA['name']} check: <{element.name}> {el_ref} — "
            f"carousel pattern, no pause control",
            level="warning"
        )

        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  f"<{element.name}> appears to be a carousel or slider "
                        f"with no detectable pause/stop mechanism.{autoplay_note} "
                        f"Auto-advancing carousels require a pause control per "
                        f"WCAG 2.2.2. {el_ref}. "
                        f"Note: static HTML analysis cannot confirm auto-advance "
                        f"behavior — manual verification required.",
            "element":  str(element)[:120],
            "fix_hint": METADATA["fix_hint"],
            "line":   getattr(element, 'sourceline', None),
            "parent": "",
            "url":      url,
        })

    # Pattern 2: role="region" or role="group" with carousel aria-labels.
    for element in soup.find_all(attrs={"role": True}):
        if id(element) in reported:
            continue
        role = element.get("role", "").lower()
        if role not in ("region", "group", "listbox"):
            continue
        aria_label = element.get("aria-label", "").lower()
        aria_labelledby = element.get("aria-labelledby", "")
        label_text = aria_label
        if aria_labelledby:
            target = soup.find(id=aria_labelledby)
            if target:
                label_text += " " + target.get_text(strip=True).lower()

        if not any(pattern in label_text for pattern in CAROUSEL_ARIA_PATTERNS):
            continue
        if _has_pause_control(element):
            continue

        reported.add(id(element))

        el_id  = element.get("id", "")
        el_ref = f'id="{el_id}"' if el_id else f'role="{role}" aria-label="{aria_label}"'

        masLog(
            f"{METADATA['name']} check: <{element.name}> {el_ref} — "
            f"carousel ARIA region, no pause control",
            level="warning"
        )

        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  f"<{element.name}> has ARIA attributes suggesting a carousel "
                        f"or slideshow region with no detectable pause/stop control. "
                        f"If content auto-advances, a pause mechanism is required "
                        f"per WCAG 2.2.2. {el_ref}. "
                        f"Manual verification required.",
            "element":  str(element)[:120],
            "fix_hint": METADATA["fix_hint"],
            "line":   getattr(element, 'sourceline', None),
            "parent": "",
            "url":      url,
        })

    if not findings:
        masLog(f"{METADATA['name']} check: passed — no carousel patterns without pause controls detected")

    return findings