# checks/mailto_warning.py
# Check 33: Mailto links without email client warning.
# WCAG 2.1 Success Criterion 2.4.4 — Link Purpose (Level A)
#
# Links with href="mailto:..." open the user's default email client
# when activated. This is unexpected behavior for users who:
#   - Don't have an email client configured (common on work computers)
#   - Are using a public or shared computer
#   - Have accessibility software that doesn't handle protocol switches well
#   - Are on mobile devices where the behavior may differ
#
# WCAG 2.4.4 requires that link purpose can be determined from the link
# text alone or from the link text with its context. A mailto link that
# just says "Contact us" or "Email" gives no indication that activating
# it will open an external application.
#
# The warning can be provided in several ways:
#   - In the link text: "Email us (opens email client)"
#   - Via aria-label: aria-label="Contact us via email (opens email client)"
#   - Via a visible parenthetical adjacent to the link
#   - Via a title attribute (less reliable — not all screen readers announce it)

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "Mailto Link Warning",
    "wcag":     "2.4.4",
    "level":    "A",
    "severity": config.SEVERITY_LOW,
    "fix_hint": "Add a warning to mailto links indicating they will open an "
                "email client. Options: (1) Include it in the link text: "
                "\"Email us (opens email client)\". "
                "(2) Use aria-label: aria-label=\"Email us, opens your email client\". "
                "(3) Add a visible note adjacent to the link. "
                "The email address itself in the link text (e.g. info@example.com) "
                "is acceptable as it implies an email action.",
}

# Warning phrases that indicate the mailto behavior is communicated.
# Checked case-insensitively against link text and aria-label combined.
WARNING_PATTERNS = [
    "email client",
    "opens email",
    "open email",
    "opens your email",
    "mail client",
    "opens mail",
]


def _has_email_address_in_text(text: str) -> bool:
    """
    Check if the link text contains an email address.

    An email address in the link text (e.g. "info@example.com")
    inherently communicates that clicking will trigger email behavior.

    Parameters:
        text (str): Lowercased link text.

    Returns:
        bool: True if text contains an @ symbol suggesting an email address.
    """
    return "@" in text


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Check mailto links for a warning that they open an email client.

    A finding is NOT raised if:
      - The link text contains an email address (@ symbol)
      - The link text or aria-label contains a warning phrase

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding per mailto link missing an email client warning.
    """

    masLog(f"Running check: {METADATA['name']}")

    findings = []

    for link in soup.find_all("a", href=True):
        href = link.get("href", "").strip().lower()

        if not href.startswith("mailto:"):
            continue

        text       = link.get_text(strip=True)
        aria_label = link.get("aria-label", "")
        combined   = (text + " " + aria_label).lower()

        # Pass if the link text contains an email address.
        if _has_email_address_in_text(combined):
            continue

        # Pass if a warning phrase is present.
        if any(pattern in combined for pattern in WARNING_PATTERNS):
            continue

        # Extract the email address from href for the finding message.
        email_addr = link.get("href", "").replace("mailto:", "").split("?")[0]
        display_text = text[:40] if text else "[no text]"

        masLog(
            f"{METADATA['name']} check: mailto:{email_addr} has no email client warning",
            level="warning"
        )

        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  f"Mailto link has no warning that it opens an email client. "
                        f"Users without a configured email client will experience "
                        f"unexpected behavior. "
                        f"Link text: \"{display_text}\", "
                        f"href: \"mailto:{email_addr}\"",
            "element":  str(link)[:120],
            "fix_hint": METADATA["fix_hint"],
            "line":   getattr(link, 'sourceline', None),
            "parent": "",
            "url":      url,
        })

    if not findings:
        masLog(f"{METADATA['name']} check: passed — all mailto links have appropriate warnings")

    return findings

