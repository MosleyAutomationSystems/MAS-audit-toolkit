# checks/skip_link_target.py
# Check 27: Skip link href target ID validation.
# WCAG 2.1 Success Criterion 2.4.1 — Bypass Blocks (Level A)
#
# Check 13 (skip_link.py) verifies that a skip link exists on the page.
# This check goes one step further: it validates that the skip link's
# href target actually exists as an element ID on the page.
#
# A broken skip link — one that points to a non-existent ID — is worse
# than no skip link at all. It creates a false affordance: keyboard users
# activate the skip link expecting to jump to main content, but nothing
# happens. The focus either stays in place or jumps to the top of the page,
# forcing users to tab through all navigation anyway.
#
# Common causes:
#   - Skip link href="#main-content" but the target has id="main" instead
#   - Target ID was renamed during a CMS update
#   - Template includes a skip link but the theme doesn't include the target
#
# This check runs independently of skip_link.py. If no skip link is found,
# this check passes silently — the missing skip link is already flagged
# by skip_link.py.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "Skip Link Target Validation",
    "wcag":     "2.4.1",
    "level":    "A",
    "severity": config.SEVERITY_HIGH,
    "fix_hint": "Ensure the skip link href target ID exists on the page. "
                "If the skip link is <a href=\"#main-content\">, there must be "
                "an element with id=\"main-content\" on the same page. "
                "Common fix: add id=\"main-content\" to your <main> element: "
                "<main id=\"main-content\">. "
                "Also ensure the target element can receive focus — add "
                "tabindex=\"-1\" if it is not naturally focusable.",
}

# Text patterns that identify a skip link — same as skip_link.py.
SKIP_LINK_PATTERNS = [
    "skip to main",
    "skip to content",
    "skip navigation",
    "skip nav",
    "skip to primary",
]


def _find_skip_links(soup: BeautifulSoup) -> list:
    """
    Find all skip navigation links on the page.

    Returns a list of anchor elements whose text or aria-label matches
    known skip link patterns.

    Parameters:
        soup (BeautifulSoup): Parsed HTML document.

    Returns:
        list: BeautifulSoup anchor elements identified as skip links.
    """
    skip_links = []
    for link in soup.find_all("a", href=True):
        text  = link.get_text(strip=True).lower()
        aria  = link.get("aria-label", "").lower()
        label = text + " " + aria
        if any(pattern in label for pattern in SKIP_LINK_PATTERNS):
            skip_links.append(link)
    return skip_links


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Validate that skip link href targets exist on the page.

    If no skip link is found, returns empty list — missing skip link
    is already flagged by skip_link.py.

    If a skip link is found but its href target ID does not exist as
    an element on the page, a HIGH severity finding is raised.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding per skip link with a broken target.
    """

    masLog(f"Running check: {METADATA['name']}")

    skip_links = _find_skip_links(soup)

    if not skip_links:
        masLog(f"{METADATA['name']} check: no skip links found — skipping target validation")
        return []

    findings = []

    for link in skip_links:
        href = link.get("href", "").strip()

        if not href.startswith("#"):
            # External or relative href — not an ID anchor, skip.
            continue

        target_id = href[1:]  # Strip the leading #

        if not target_id:
            # href="#" with no ID — broken by definition.
            masLog(
                f"{METADATA['name']} check: skip link has empty href target",
                level="warning"
            )
            findings.append({
                "check":    METADATA["name"],
                "wcag":     METADATA["wcag"],
                "level":    METADATA["level"],
                "severity": METADATA["severity"],
                "message":  "Skip link has href=\"#\" with no target ID. "
                            "Activating this link does nothing — keyboard users "
                            "receive no benefit from the skip link.",
                "element":  str(link)[:120],
                "fix_hint": METADATA["fix_hint"],
                "line":   getattr(link, 'sourceline', None),
                "parent": "",
                "url":      url,
            })
            continue

        # Check whether the target ID exists on the page.
        target = soup.find(id=target_id)

        if target is not None:
            masLog(f"{METADATA['name']} check: skip link target #{target_id} found — passed")
            continue

        masLog(
            f"{METADATA['name']} check: skip link target #{target_id} not found on page",
            level="warning"
        )

        link_text = link.get_text(strip=True)[:40]

        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  f"Skip link points to #{target_id} but no element with "
                        f"id=\"{target_id}\" exists on the page. The skip link is "
                        f"broken — keyboard users activate it but focus does not move. "
                        f"Link text: \"{link_text}\"",
            "element":  str(link)[:120],
            "fix_hint": METADATA["fix_hint"],
            "line":   getattr(link, 'sourceline', None),
            "parent": "",
            "url":      url,
        })

    if not findings:
        masLog(f"{METADATA['name']} check: passed — all skip link targets exist on the page")

    return findings

