# checks/multiple_nav_labels.py
# Check 26: Multiple nav elements missing distinguishing aria-label.
# WCAG 2.1 Success Criterion 2.4.1 — Bypass Blocks (Level A)
#
# When a page has more than one <nav> landmark, screen reader users
# navigating by landmarks cannot distinguish between them. Both appear
# as "navigation" in the landmarks list, giving users no way to know
# which is the main navigation and which is a secondary, footer, or
# breadcrumb navigation.
#
# The fix is simple: add an aria-label or aria-labelledby attribute to
# each nav element to give it a unique, descriptive name.
#
# Examples:
#   <nav aria-label="Main navigation">...</nav>
#   <nav aria-label="Breadcrumb">...</nav>
#   <nav aria-label="Footer links">...</nav>
#
# A page with only one <nav> element does not need an aria-label —
# it is unambiguously "the navigation" on that page. This check only
# fires when two or more nav elements are present and unlabeled.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "Multiple Nav Label Check",
    "wcag":     "2.4.1",
    "level":    "A",
    "severity": config.SEVERITY_MEDIUM,
    "fix_hint": "Add a unique aria-label to each <nav> element when a page "
                "has more than one navigation landmark. The label should describe "
                "the purpose of that navigation region. Examples: "
                "aria-label=\"Main navigation\", aria-label=\"Breadcrumb\", "
                "aria-label=\"Footer links\", aria-label=\"Table of contents\". "
                "Alternatively, use aria-labelledby pointing to a visible heading "
                "inside the nav element.",
}


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Check whether multiple <nav> elements have distinguishing aria-labels.

    If only one <nav> is present, no finding is raised — a single nav
    landmark is unambiguous. If two or more are present, each one missing
    an aria-label or aria-labelledby is flagged.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding per unlabeled nav when multiple navs are present.
    """

    masLog(f"Running check: {METADATA['name']}")

    nav_elements = soup.find_all("nav")

    # Also check role="navigation" on non-nav elements.
    role_navs = soup.find_all(
        lambda tag: tag.get("role", "").strip().lower() == "navigation"
        and tag.name != "nav"
    )

    all_navs = nav_elements + role_navs

    if len(all_navs) < 2:
        masLog(f"{METADATA['name']} check: passed — fewer than 2 nav elements found")
        return []

    findings = []

    for i, nav in enumerate(all_navs, start=1):
        aria_label      = nav.get("aria-label", "").strip()
        aria_labelledby = nav.get("aria-labelledby", "").strip()

        if aria_label or aria_labelledby:
            continue

        # Build element identifier.
        nav_id    = nav.get("id", "")
        nav_class = " ".join(nav.get("class", []))
        el_ref    = (
            f'id="{nav_id}"' if nav_id
            else f'class="{nav_class}"' if nav_class
            else f"nav #{i} of {len(all_navs)}"
        )

        masLog(
            f"{METADATA['name']} check: {el_ref} missing aria-label",
            level="warning"
        )

        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  f"Page has {len(all_navs)} navigation landmarks but "
                        f"{el_ref} has no aria-label or aria-labelledby. "
                        f"Screen reader users cannot distinguish between navigation "
                        f"regions when browsing by landmarks.",
            "element":  str(nav)[:120],
            "fix_hint": METADATA["fix_hint"],
            "line":   getattr(nav, 'sourceline', None),
            "parent": "",
            "url":      url,
        })

    if not findings:
        masLog(f"{METADATA['name']} check: passed — all nav elements have distinguishing labels")

    return findings

