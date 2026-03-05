# checks/alt_text.py
# Check 1: Missing or empty alt attributes on <img> elements.
# WCAG 2.1 Success Criterion 1.1.1 — Non-text Content (Level A)
# Every <img> must have an alt attribute. Decorative images must use alt=""
# explicitly. A missing alt attribute is always a failure.

from bs4 import BeautifulSoup
from utils.logger import masLog

def check_alt_text(soup: BeautifulSoup) -> list:
    """
    Find all <img> elements missing a valid alt attribute.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.

    Returns:
        list: A list of finding dictionaries. Each dictionary describes
              one failing <img> element. Empty list means no issues found.
    """

    masLog("Running check: alt text on <img> elements")

    # findings is the list we will return. Each item will be a dictionary
    # describing one issue found. We start empty and add to it as we find problems.
    findings = []

    # soup.find_all("img") returns a list of every <img> tag in the document.
    # BeautifulSoup parses the HTML tree and lets us search it by tag name.
    images = soup.find_all("img")

    masLog(f"Found {len(images)} <img> element(s) to check")

    # Loop through every image and check its alt attribute.
    for img in images:
        # img.get("alt") retrieves the alt attribute value.
        # If the attribute does not exist at all, it returns None.
        alt = img.get("alt")

        # We only flag images where alt is completely absent (None).
        # alt="" is valid — it tells screen readers the image is decorative.
        # alt="some text" is valid — it describes the image.
        # Only a missing attribute entirely is a failure here.
        if alt is None:
            # img.get("src", "[no src]") gets the src attribute for context.
            # We include it in the finding so the report tells the user
            # which specific image is the problem.
            src = img.get("src", "[no src attribute]")

            # Build a finding dictionary with consistent keys.
            # Every check in this toolkit returns findings in this same format
            # so the report writer can handle them all the same way.
            finding = {
                "check": "Alt Text",
                "wcag": "1.1.1",
                "level": "A",
                "severity": "error",
                "message": f'<img> missing alt attribute — src="{src}"'
            }

            findings.append(finding)

    # Log a summary before returning.
    if findings:
        masLog(f"Alt text check: {len(findings)} issue(s) found", level="warning")
    else:
        masLog("Alt text check: passed — no issues found")

    return findings