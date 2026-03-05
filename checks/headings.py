# checks/headings.py
# Check 2: <h1> count — there must be exactly one <h1> per page.
# Check 3: Heading descent — headings must not skip levels (e.g. h1 -> h3).
# WCAG 2.1 Success Criterion 1.3.1 — Info and Relationships (Level A)
# WCAG 2.1 Success Criterion 2.4.6 — Headings and Labels (Level AA)
# Both checks are in one file because they both operate on the same
# heading data — no need to parse the document twice.

from bs4 import BeautifulSoup
from utils.logger import masLog

def check_headings(soup: BeautifulSoup) -> list:
    """
    Run both heading checks: h1 count and heading descent order.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.

    Returns:
        list: A list of finding dictionaries describing any issues found.
    """

    masLog("Running check: heading structure")

    findings = []

    # soup.find_all() accepts a list of tag names.
    # This returns every h1 through h6 in document order —
    # the same order a screen reader would encounter them.
    headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])

    masLog(f"Found {len(headings)} heading element(s) to check")

    # --- Check 2: h1 count ---

    # Filter the full heading list down to only h1 elements.
    h1_tags = [h for h in headings if h.name == "h1"]

    if len(h1_tags) == 0:
        # No h1 at all — the page has no primary heading.
        findings.append({
            "check": "Heading Structure",
            "wcag": "1.3.1",
            "level": "A",
            "severity": "error",
            "message": "Page has no <h1> element — every page must have exactly one"
        })

    elif len(h1_tags) > 1:
        # Multiple h1s — the page has ambiguous primary structure.
        findings.append({
            "check": "Heading Structure",
            "wcag": "1.3.1",
            "level": "A",
            "severity": "error",
            "message": f"Page has {len(h1_tags)} <h1> elements — there must be exactly one"
        })

    # --- Check 3: Heading descent ---

    # We walk through the headings in order, tracking the numeric level
    # of the previous heading. A jump from h2 to h4 (skipping h3) is a failure.
    # We start prev_level at 0 so the first heading (whatever it is) is always
    # accepted without triggering a false skip warning.
    prev_level = 0

    for heading in headings:
        # heading.name is the tag name string: "h1", "h2", etc.
        # int(heading.name[1]) extracts the numeric level from the tag name.
        # "h1"[1] = "1", int("1") = 1.
        current_level = int(heading.name[1])

        # A skip is when the current level is more than one step deeper
        # than the previous level. h2 -> h4 is a skip (difference of 2).
        # h2 -> h3 is fine (difference of 1).
        # h3 -> h2 is fine — going back up is always allowed.
        if current_level > prev_level + 1 and prev_level != 0:

            # heading.get_text() extracts the visible text content of the tag,
            # stripped of any inner HTML. We include it so the report shows
            # which specific heading caused the skip.
            text = heading.get_text(strip=True)

            findings.append({
                "check": "Heading Structure",
                "wcag": "2.4.6",
                "level": "AA",
                "severity": "error",
                "message": (
                    f"Heading level skipped — jumped from h{prev_level} "
                    f"to h{current_level}: \"{text}\""
                )
            })

        # Update prev_level for the next iteration.
        prev_level = current_level

    if findings:
        masLog(f"Heading check: {len(findings)} issue(s) found", level="warning")
    else:
        masLog("Heading check: passed — no issues found")

    return findings