# checks/labels.py
# Check 4: Missing <label> associations on <input> elements.
# WCAG 2.1 Success Criterion 1.3.1 — Info and Relationships (Level A)
# WCAG 2.1 Success Criterion 3.3.2 — Labels or Instructions (Level A)
# Every form input must have a programmatically associated label so
# screen readers can announce what the field is for.

from bs4 import BeautifulSoup
from utils.logger import masLog

# Input types that do not require a visible label.
# submit/reset/button have their label in their value attribute.
# hidden inputs are never presented to the user.
# image inputs use alt text instead of a label.
EXEMPT_INPUT_TYPES = {"submit", "reset", "button", "hidden", "image"}

def check_labels(soup: BeautifulSoup) -> list:
    """
    Find all <input> elements that lack a proper label association.

    A label association is valid if ANY of these are true:
    1. A <label> element exists with a for= attribute matching the input's id=
    2. The <input> is nested directly inside a <label> element
    3. The <input> has an aria-label attribute
    4. The <input> has an aria-labelledby attribute

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.

    Returns:
        list: A list of finding dictionaries for unlabeled inputs.
    """

    masLog("Running check: <label> associations on <input> elements")

    findings = []

    # Find every <input> in the document.
    inputs = soup.find_all("input")

    masLog(f"Found {len(inputs)} <input> element(s) to check")

    for inp in inputs:
        # inp.get("type", "text") gets the type attribute.
        # If no type is specified, HTML defaults to "text", so we do the same.
        input_type = inp.get("type", "text").lower()

        # Skip input types that do not need a label — they are exempt by spec.
        if input_type in EXEMPT_INPUT_TYPES:
            continue

        # --- Check method 1: aria-label attribute ---
        # aria-label provides an invisible label string directly on the element.
        if inp.get("aria-label"):
            continue

        # --- Check method 2: aria-labelledby attribute ---
        # aria-labelledby points to the id of another element whose text
        # serves as the label. We accept its presence without verifying the
        # referenced element exists — that is a deeper audit step.
        if inp.get("aria-labelledby"):
            continue

        # --- Check method 3: wrapped inside a <label> ---
        # inp.find_parent("label") walks up the DOM tree looking for a
        # <label> ancestor. If found, the input is implicitly labeled.
        if inp.find_parent("label"):
            continue

        # --- Check method 4: <label for="id"> association ---
        # This requires the input to have an id, and a <label> elsewhere
        # in the document with a matching for= attribute.
        input_id = inp.get("id")
        if input_id:
            # soup.find() searches the whole document for the first match.
            # We look for a <label> whose for= attribute equals the input's id.
            matching_label = soup.find("label", attrs={"for": input_id})
            if matching_label:
                continue

        # If we reach this point, none of the four methods found a label.
        # Build a finding with enough context to locate the input in the source.
        input_name = inp.get("name", "[no name]")
        input_id_display = input_id if input_id else "[no id]"

        findings.append({
            "check": "Form Labels",
            "wcag": "1.3.1",
            "level": "A",
            "severity": "error",
            "message": (
                f'<input type="{input_type}"> missing label — '
                f'name="{input_name}", id="{input_id_display}"'
            )
        })

    if findings:
        masLog(f"Label check: {len(findings)} issue(s) found", level="warning")
    else:
        masLog("Label check: passed — no issues found")

    return findings