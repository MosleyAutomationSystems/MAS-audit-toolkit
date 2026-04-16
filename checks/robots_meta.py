# checks/robots_meta.py
# Check 42: Robots meta tag flagging noindex on content pages.
# Mosley Standard — Operational (MS)
#
# The robots meta tag controls whether search engines index a page and
# follow its links. When a content page has noindex, it is excluded from
# search results entirely. This is appropriate for:
#   - Admin pages, login pages, thank-you pages
#   - Duplicate content that should be canonicalized elsewhere
#   - Staging or preview pages
#
# However, noindex on a public-facing content page is almost always
# unintentional — a developer error, a CMS misconfiguration, or a
# forgotten staging setting that made it to production.
#
# From an accessibility standpoint, users who rely on search to find
# content (including users with cognitive disabilities who use search
# as a navigation strategy) cannot find noindexed pages.
#
# This is an informational (INFO) finding — it requires human judgment
# to determine whether noindex is intentional. The finding surfaces the
# issue for review, not remediation.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "Robots Meta Check",
    "wcag":     "MS",
    "level":    "MS",
    "severity": config.SEVERITY_INFO,
    "fix_hint": "Review whether noindex is intentional on this page. "
                "If the page is public-facing content that should appear in "
                "search results, remove noindex from the robots meta tag or "
                "remove the tag entirely. "
                "If noindex is intentional (login page, admin area, duplicate), "
                "no action is needed — document the reason in your audit notes. "
                "To allow indexing: <meta name=\"robots\" content=\"index, follow\"> "
                "or simply remove the robots meta tag.",
}

# Content values that restrict indexing.
NOINDEX_VALUES = {"noindex", "none"}


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Check for robots meta tags containing noindex directives.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding if a noindex directive is detected.
    """

    masLog(f"Running check: {METADATA['name']}")

    # Find all robots meta tags — both name="robots" and name="googlebot".
    robots_tags = soup.find_all(
        "meta",
        attrs={"name": lambda v: v and v.strip().lower() in ("robots", "googlebot")}
    )

    if not robots_tags:
        masLog(f"{METADATA['name']} check: passed — no robots meta tag found")
        return []

    findings = []

    for tag in robots_tags:
        content = tag.get("content", "").strip().lower()
        tag_name = tag.get("name", "robots")

        if not content:
            continue

        # Parse comma-separated directives.
        directives = [d.strip() for d in content.split(",")]

        for directive in directives:
            if directive in NOINDEX_VALUES:
                masLog(
                    f"{METADATA['name']} check: {tag_name} contains {directive}",
                    level="warning"
                )

                findings.append({
                    "check":    METADATA["name"],
                    "wcag":     METADATA["wcag"],
                    "level":    METADATA["level"],
                    "severity": METADATA["severity"],
                    "message":  f"<meta name=\"{tag_name}\" content=\"{content}\"> "
                                f"contains \"{directive}\" — this page is excluded from "
                                f"search engine indexes. If this is a public content page, "
                                f"this may be unintentional. Review required.",
                    "element":  str(tag)[:120],
                    "fix_hint": METADATA["fix_hint"],
                    "line":   getattr(tag, 'sourceline', None),
                    "parent": "",
                    "url":      url,
                })
                break  # One finding per tag.

    if not findings:
        masLog(f"{METADATA['name']} check: passed — no noindex directives detected")

    return findings

