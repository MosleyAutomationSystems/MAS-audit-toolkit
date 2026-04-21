# checks/viewport_meta.py
# Check 16: Viewport meta tag restricts user scaling.
# WCAG 2.1 Success Criterion 1.4.4 — Resize Text (Level A)
# The viewport meta tag controls how browsers scale content on mobile devices.
# Setting user-scalable=no or maximum-scale=1 prevents users from zooming,
# which blocks access for low-vision users who rely on browser zoom to read
# content. This is one of the most common mobile accessibility failures.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "Viewport Meta Check",
    "wcag":     "1.4.4",
    "level":    "A",
    "severity": config.SEVERITY_CRITICAL,
    "fix_hint": "Remove user-scalable=no and any maximum-scale value below 5 "
                "from the viewport meta tag. The safe viewport declaration is: "
                '<meta name="viewport" content="width=device-width, '
                'initial-scale=1">. Never restrict user scaling — '
                "low-vision users depend on browser zoom to read content.",
}

# maximum-scale values at or below this threshold are flagged.
# WCAG requires content to be zoomable to at least 200% (scale factor 2.0).
# Values of 1.0 completely prevent zooming. Values below 2.0 restrict it.
# We flag anything at or below 2.0 to be conservative and catch borderline cases.
MAX_SCALE_THRESHOLD = 2.0


def _parse_viewport_content(content: str) -> dict:
    """
    Parse a viewport meta content string into a key-value dict.

    Handles comma-separated pairs with optional whitespace.
    Example: "width=device-width, initial-scale=1, user-scalable=no"
    Returns: {"width": "device-width", "initial-scale": "1", "user-scalable": "no"}

    Parameters:
        content (str): Raw content attribute value from the viewport meta tag.

    Returns:
        dict: Parsed key-value pairs, all keys and values lowercased.
    """
    pairs = {}
    for part in content.split(","):
        part = part.strip()
        if "=" in part:
            key, _, val = part.partition("=")
            pairs[key.strip().lower()] = val.strip().lower()
    return pairs


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Check the viewport meta tag for user scaling restrictions.

    Flags two specific conditions:
      1. user-scalable=no — explicitly disables pinch-to-zoom entirely.
      2. maximum-scale <= 2.0 — prevents users from reaching 200% zoom.

    One finding is raised per violation. Both can fire on the same page
    if the viewport tag contains both restrictions simultaneously.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: Zero, one, or two findings depending on violations found.
    """

    masLog(f"Running check: {METADATA['name']}")

    findings = []

    # Locate the viewport meta tag.
    # Some pages have multiple meta tags — find the one with name="viewport".
    viewport = soup.find("meta", attrs={"name": lambda v: v and v.lower() == "viewport"})

    if viewport is None:
        # No viewport tag at all — not flagged here.
        # Missing viewport is a separate concern (mobile layout, not scaling restriction).
        masLog(f"{METADATA['name']} check: passed — no viewport tag present")
        return []

    content = viewport.get("content", "")
    if not content.strip():
        masLog(f"{METADATA['name']} check: passed — viewport tag has no content")
        return []

    props = _parse_viewport_content(content)
    element_str = f'<meta name="viewport" content="{content}">'

    # Check 1: user-scalable=no
    user_scalable = props.get("user-scalable", "")
    if user_scalable in ("no", "0"):
        masLog(
            f"{METADATA['name']} check: user-scalable=no detected",
            level="warning"
        )
        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  "Viewport meta sets user-scalable=no. This disables "
                        "pinch-to-zoom entirely, blocking low-vision users who "
                        "rely on browser zoom to read content.",
            "element":  element_str,
            "fix_hint": METADATA["fix_hint"],
            "line":   None,
            "parent": "",
            "url":      url,
        })

    # Check 2: maximum-scale <= 2.0
    max_scale_raw = props.get("maximum-scale", "")
    if max_scale_raw:
        try:
            max_scale = float(max_scale_raw)
            if max_scale <= MAX_SCALE_THRESHOLD:
                masLog(
                    f"{METADATA['name']} check: maximum-scale={max_scale} detected",
                    level="warning"
                )
                findings.append({
                    "check":    METADATA["name"],
                    "wcag":     METADATA["wcag"],
                    "level":    METADATA["level"],
                    "severity": METADATA["severity"],
                    "message":  f"Viewport meta sets maximum-scale={max_scale}. "
                                "WCAG 1.4.4 requires content to be zoomable to at "
                                "least 200%. This restriction prevents low-vision "
                                "users from reaching the minimum required zoom level.",
                    "element":  element_str,
                    "fix_hint": METADATA["fix_hint"],
                    "line":   None,
                    "parent": "",
                    "url":      url,
                })
        except ValueError:
            # Non-numeric maximum-scale value — log and skip, not a crash condition.
            masLog(
                f"{METADATA['name']} check: non-numeric maximum-scale value '{max_scale_raw}' — skipped",
                level="warning"
            )

    if not findings:
        masLog(f"{METADATA['name']} check: passed — no scaling restrictions detected")

    return findings

