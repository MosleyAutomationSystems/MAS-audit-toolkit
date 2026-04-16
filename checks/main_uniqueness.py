# checks/main_uniqueness.py
# Check 28: Multiple <main> elements on a single page.
# WCAG 2.1 Success Criterion 1.3.1 — Info and Relationships (Level A)
#
# The <main> element identifies the primary content of a page. There must
# be exactly one visible <main> element per page. Multiple <main> elements
# create ambiguity for screen readers and violate the HTML specification.
#
# Screen readers expose landmark regions to users so they can jump directly
# to main content. If two <main> elements exist, assistive technologies
# may announce both, leaving users confused about which contains the
# primary content.
#
# The HTML spec does allow multiple <main> elements if all but one are
# hidden with the hidden attribute. This check accounts for that exception
# and only flags visible <main> elements.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "Main Uniqueness Check",
    "wcag":     "1.3.1",
    "level":    "A",
    "severity": config.SEVERITY_HIGH,
    "fix_hint": "Ensure each page has exactly one visible <main> element. "
                "If your page uses JavaScript to show/hide content sections, "
                "use the hidden attribute on inactive <main> elements rather "
                "than CSS display:none or visibility:hidden — the HTML spec "
                "permits multiple <main> elements as long as only one is visible "
                "(not hidden). Remove duplicate <main> elements or restructure "
                "the page so secondary content uses <section> or <article> instead.",
}


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Check that the page has exactly one visible <main> element.

    Hidden <main> elements (with the hidden attribute) are excluded
    per the HTML specification, which permits multiple <main> elements
    as long as only one is visible at a time.

    Also checks for elements with role="main" that are not <main> tags.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding if more than one visible main element is detected.
    """

    masLog(f"Running check: {METADATA['name']}")

    # Find all <main> elements not hidden via the hidden attribute.
    all_mains = soup.find_all("main")
    visible_mains = [m for m in all_mains if m.get("hidden") is None]

    # Also find role="main" on non-main elements.
    role_mains = soup.find_all(
        lambda tag: tag.get("role", "").strip().lower() == "main"
        and tag.name != "main"
        and tag.get("hidden") is None
    )

    all_visible = visible_mains + role_mains

    if len(all_visible) <= 1:
        masLog(f"{METADATA['name']} check: passed — {len(all_visible)} visible main element(s) found")
        return []

    masLog(
        f"{METADATA['name']} check: {len(all_visible)} visible main elements detected",
        level="warning"
    )

    # Build a summary of the duplicate elements.
    el_summaries = []
    for i, m in enumerate(all_visible, start=1):
        m_id    = m.get("id", "")
        m_class = " ".join(m.get("class", []))
        ref     = (
            f'id="{m_id}"' if m_id
            else f'class="{m_class}"' if m_class
            else f"<{m.name}> #{i}"
        )
        el_summaries.append(ref)

    return [{
        "check":    METADATA["name"],
        "wcag":     METADATA["wcag"],
        "level":    METADATA["level"],
        "severity": METADATA["severity"],
        "message":  f"Page has {len(all_visible)} visible <main> elements — "
                    f"there must be exactly one. Screen readers may announce multiple "
                    f"main landmarks, confusing users about where the primary content is. "
                    f"Elements found: {', '.join(el_summaries)}.",
        "element":  str(all_visible[0])[:120],
        "fix_hint": METADATA["fix_hint"],
        "line":   None,
        "parent": "",
        "url":      url,
    }]

