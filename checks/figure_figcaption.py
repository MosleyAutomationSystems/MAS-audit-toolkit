# checks/figure_figcaption.py
# Check 19: Figure elements missing figcaption.
# WCAG 2.1 Success Criterion 1.1.1 — Non-text Content (Level A)
#
# The <figure> element is used to mark up self-contained content —
# images, diagrams, code blocks, or charts — that is referenced from
# the main content. A <figcaption> provides a visible, programmatic
# caption that screen readers associate with the figure.
#
# Without a figcaption, sighted users may have context that blind users
# do not. This is especially problematic for informational images,
# charts, and diagrams where the caption provides essential meaning.
#
# Note: A <figure> containing an <img> with a descriptive alt attribute
# partially satisfies 1.1.1, but a figcaption is still best practice
# for providing visible context to all users. This check flags the
# absence of figcaption as a medium-severity finding to prompt review.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "Figure/Figcaption Check",
    "wcag":     "1.1.1",
    "level":    "A",
    "severity": config.SEVERITY_MEDIUM,
    "fix_hint": "Add a <figcaption> inside every <figure> element to provide "
                "a visible caption that describes the content. Place it as the "
                "first or last child of the <figure>. Example: "
                "<figure><img src='chart.png' alt='Bar chart showing Q1 revenue'>"
                "<figcaption>Q1 2026 Revenue by Region</figcaption></figure>. "
                "The figcaption supplements the alt text — alt describes the image "
                "for screen readers, figcaption provides visible context for all users.",
}


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Check all <figure> elements for a <figcaption> child.

    Flags any <figure> that has no <figcaption> descendant.
    Empty figcaptions (whitespace only) are also flagged.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding per <figure> element missing a valid figcaption.
    """

    masLog(f"Running check: {METADATA['name']}")

    findings = []

    figures = soup.find_all("figure")

    if not figures:
        masLog(f"{METADATA['name']} check: passed — no <figure> elements found")
        return []

    for figure in figures:
        figcaption = figure.find("figcaption")

        # Check for missing or empty figcaption.
        if figcaption is None:
            issue = "missing <figcaption>"
        elif not figcaption.get_text(strip=True):
            issue = "empty <figcaption>"
        else:
            continue

        # Build a readable identifier from the figure's contents.
        img = figure.find("img")
        if img:
            src      = img.get("src", "[no src]")
            alt      = img.get("alt", "[no alt]")
            el_ref   = f'img src="{src[:60]}" alt="{alt[:40]}"'
        else:
            inner_text = figure.get_text(strip=True)[:40]
            el_ref     = f'text="{inner_text}"' if inner_text else "[no content]"

        masLog(
            f"{METADATA['name']} check: <figure> with {el_ref} has {issue}",
            level="warning"
        )

        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  f"<figure> element has {issue} — sighted users may have "
                        f"visual context that screen reader users do not. {el_ref}",
            "element":  str(figure)[:120],
            "fix_hint": METADATA["fix_hint"],
            "line":   getattr(figure, 'sourceline', None),
            "parent": "",
            "url":      url,
        })

    if not findings:
        masLog(f"{METADATA['name']} check: passed — all <figure> elements have valid figcaptions")

    return findings

