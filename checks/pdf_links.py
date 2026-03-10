# checks/pdf_links.py
# Check 10: Links pointing to PDF files without a warning in the link text.
# WCAG 2.1 Success Criterion 2.4.4 — Link Purpose (Level A)
# PDFs open in a separate viewer, may not be accessible, and behave
# differently from standard web pages. Users should be warned before
# following a PDF link so they can make an informed choice.
# Best practice: include "(PDF)" or file size in the link text.

from bs4 import BeautifulSoup
from utils.logger import masLog
import config
METADATA = {
    "name":     "PDF Link Warning",
    "wcag":     "2.4.4",
    "level":    "A",
    "severity": config.SEVERITY_LOW,
    "fix_hint": 'Add "(PDF)" to the link text so users know the link opens a PDF — for example: "Annual Report (PDF)".',
}
# Warning indicators we accept as sufficient user notice in link text.
# Case-insensitive match is applied when checking.
PDF_WARNING_INDICATORS = ["pdf", "document", "download"]

def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Find links pointing to PDF files whose text does not warn the user.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.

    Returns:
        list: A list of finding dictionaries for each unwarned PDF link.
    """

    masLog(f"Running check: {METADATA['name']}")

    findings = []

    # Find all anchor tags with an href attribute.
    links = soup.find_all("a", href=True)

    masLog(f"Found {len(links)} link(s) to check for PDF destinations")

    for link in links:
        href = link.get("href", "").strip().lower()

        # Only process links whose href ends in .pdf.
        if not href.endswith(".pdf"):
            continue

        # Get the full accessible name of the link —
        # visible text first, then aria-label as fallback.
        text = link.get_text(strip=True).lower()
        aria = link.get("aria-label", "").lower()
        full_label = text + " " + aria

        # Check whether any warning indicator appears in the label.
        # If the user wrote "Annual Report (PDF)" or "Download report",
        # they have provided sufficient context — we do not flag it.
        warned = any(
            indicator in full_label
            for indicator in PDF_WARNING_INDICATORS
        )

        if not warned:
            # Restore original href for display (not lowercased).
            display_href = link.get("href", "[no href]")
            display_text = link.get_text(strip=True) or "[no text]"

            findings.append({
                "check":    METADATA["name"],
                "wcag":     METADATA["wcag"],
                "level":    METADATA["level"],
                "severity": METADATA["severity"],
                "message":  f'Link points to a PDF but does not warn the user — add "(PDF)" to the link text. text="{display_text}", href="{display_href}"',
                "element":  str(link),
                "fix_hint": METADATA["fix_hint"],
                "url":      url,
            })

    if findings:
        masLog(f"PDF link check: {len(findings)} issue(s) found", level="warning")
    else:
        masLog("PDF link check: passed — all PDF links include user warning")

    return findings
