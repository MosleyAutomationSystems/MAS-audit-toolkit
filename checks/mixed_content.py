# checks/mixed_content.py
# Check 43: HTTP resources on HTTPS pages.
# Mosley Standard — Security/Operational (MS)
#
# Mixed content occurs when an HTTPS page loads resources (images, scripts,
# stylesheets, iframes) over HTTP. This creates security and reliability issues:
#
# Active mixed content (scripts, iframes, stylesheets):
#   - Blocked by modern browsers by default
#   - Can expose users to man-in-the-middle attacks
#   - May silently break page functionality
#
# Passive mixed content (images, audio, video):
#   - May still load but triggers browser security warnings
#   - Can expose user browsing behavior to network observers
#   - Images may fail in strict security environments
#
# From an accessibility standpoint, broken images produce missing alt text
# in practice, and blocked scripts can break keyboard navigation and ARIA
# functionality that is JavaScript-dependent.
#
# This check only fires when the audited URL is HTTPS and HTTP resource
# references are found in the HTML. For local file audits, it is skipped.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "Mixed Content Check",
    "wcag":     "MS",
    "level":    "MS",
    "severity": config.SEVERITY_HIGH,
    "fix_hint": "Replace all HTTP resource URLs with HTTPS equivalents. "
                "For images: change src=\"http://\" to src=\"https://\". "
                "For scripts: change src=\"http://\" to src=\"https://\". "
                "For stylesheets: change href=\"http://\" to href=\"https://\". "
                "If the resource host does not support HTTPS, find an alternative "
                "source or self-host the resource. "
                "Use protocol-relative URLs (//example.com/resource) only as a "
                "last resort — prefer explicit https://.",
}

# Resource attributes to check for HTTP references.
RESOURCE_ATTRS = [
    ("img",    "src"),
    ("script", "src"),
    ("link",   "href"),
    ("iframe", "src"),
    ("audio",  "src"),
    ("video",  "src"),
    ("source", "src"),
    ("source", "srcset"),
]


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Check for HTTP resource references on an HTTPS page.

    Skips the check if the audited URL is not HTTPS or is a local file.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding per HTTP resource reference found.
    """

    masLog(f"Running check: {METADATA['name']}")

    # Only check HTTPS pages — mixed content is only an issue on secure pages.
    if not url.lower().startswith("https://"):
        masLog(f"{METADATA['name']} check: skipped — URL is not HTTPS")
        return []

    findings = []

    for tag_name, attr_name in RESOURCE_ATTRS:
        for element in soup.find_all(tag_name, attrs={attr_name: True}):
            attr_val = element.get(attr_name, "").strip()

            if not attr_val.lower().startswith("http://"):
                continue

            # Build element identifier.
            el_id  = element.get("id", "")
            el_ref = f'id="{el_id}"' if el_id else f"<{tag_name}>"

            # Classify severity by resource type.
            # Active mixed content (scripts, stylesheets, iframes) is more
            # dangerous than passive (images, media).
            if tag_name in ("script", "link", "iframe"):
                severity = config.SEVERITY_CRITICAL
                content_type = "active"
            else:
                severity = config.SEVERITY_HIGH
                content_type = "passive"

            masLog(
                f"{METADATA['name']} check: {content_type} mixed content — "
                f"<{tag_name} {attr_name}=\"{attr_val[:60]}\">",
                level="warning"
            )

            findings.append({
                "check":    METADATA["name"],
                "wcag":     METADATA["wcag"],
                "level":    METADATA["level"],
                "severity": severity,
                "message":  f"{content_type.capitalize()} mixed content: "
                            f"<{tag_name}> loads over HTTP on an HTTPS page. "
                            f"Modern browsers block active mixed content and warn "
                            f"on passive mixed content. "
                            f"{attr_name}=\"{attr_val[:80]}\" {el_ref}",
                "element":  str(element)[:120],
                "fix_hint": METADATA["fix_hint"],
                "line":   getattr(element, 'sourceline', None),
                "parent": "",
                "url":      url,
            })

    if not findings:
        masLog(f"{METADATA['name']} check: passed — no mixed content detected")

    return findings

