# checks/aria_required_consistency.py
# Check 36: Mismatches between aria-required and HTML required attributes.
# WCAG 2.1 Success Criterion 4.1.2 — Name, Role, Value (Level A)
#
# HTML5 introduced the required attribute for form inputs. ARIA introduced
# aria-required="true" for the same purpose. When both are used, they must
# agree. A mismatch creates conflicting signals:
#
# Case 1: required but aria-required="false"
#   The browser enforces required validation, but the ARIA attribute tells
#   screen readers the field is optional. Users may submit the form expecting
#   success, only to receive a validation error they weren't warned about.
#
# Case 2: aria-required="true" but no required attribute
#   Screen readers announce the field as required, but the browser won't
#   enforce it. This is less harmful but still misleading — users may
#   feel they must fill in a field that is actually optional.
#
# The correct pattern is to use HTML required alone, or both required and
# aria-required="true" together. Never use aria-required="false" on a
# field that has the required attribute.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "aria-required Consistency",
    "wcag":     "4.1.2",
    "level":    "A",
    "severity": config.SEVERITY_HIGH,
    "fix_hint": "Ensure aria-required and the HTML required attribute are consistent. "
                "Preferred pattern: use HTML required alone — browsers and screen "
                "readers both respect it. If you use both, they must agree: "
                "<input required aria-required=\"true\">. "
                "Never use aria-required=\"false\" on a field with required. "
                "Remove aria-required entirely if HTML required is present — "
                "it is redundant and a source of inconsistency.",
}


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Check form inputs for mismatches between aria-required and required.

    Flags two mismatch patterns:
      1. Has HTML required + aria-required="false" — contradictory
      2. Has aria-required="true" + no HTML required — misleading

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding per input with a conflicting required state.
    """

    masLog(f"Running check: {METADATA['name']}")

    findings = []

    input_tags = soup.find_all(["input", "select", "textarea"])

    for element in input_tags:
        # Skip hidden inputs — they are never user-facing.
        if element.get("type", "").strip().lower() == "hidden":
            continue

        has_required      = element.get("required") is not None
        aria_required_val = element.get("aria-required", "").strip().lower()
        has_aria_required = aria_required_val != ""

        if not has_aria_required:
            continue  # No aria-required — nothing to check for consistency.

        # Build element identifier.
        el_id   = element.get("id", "")
        el_name = element.get("name", "[no name]")
        el_ref  = f'id="{el_id}"' if el_id else f'name="{el_name}"'

        # Case 1: HTML required present + aria-required="false"
        if has_required and aria_required_val == "false":
            masLog(
                f"{METADATA['name']} check: <{element.name}> {el_ref} "
                f"has required but aria-required=false",
                level="warning"
            )
            findings.append({
                "check":    METADATA["name"],
                "wcag":     METADATA["wcag"],
                "level":    METADATA["level"],
                "severity": METADATA["severity"],
                "message":  f"<{element.name}> has HTML required but "
                            f"aria-required=\"false\" — contradictory signals. "
                            f"The browser enforces required validation but "
                            f"screen readers announce the field as optional. "
                            f"{el_ref}",
                "element":  str(element)[:120],
                "fix_hint": METADATA["fix_hint"],
                "line":   getattr(element, 'sourceline', None),
                "parent": "",
                "url":      url,
            })

        # Case 2: aria-required="true" + no HTML required
        elif aria_required_val == "true" and not has_required:
            masLog(
                f"{METADATA['name']} check: <{element.name}> {el_ref} "
                f"has aria-required=true but no HTML required",
                level="warning"
            )
            findings.append({
                "check":    METADATA["name"],
                "wcag":     METADATA["wcag"],
                "level":    METADATA["level"],
                "severity": METADATA["severity"],
                "message":  f"<{element.name}> has aria-required=\"true\" but "
                            f"no HTML required attribute. Screen readers announce "
                            f"the field as required but the browser won't enforce it — "
                            f"misleading for all users. {el_ref}",
                "element":  str(element)[:120],
                "fix_hint": METADATA["fix_hint"],
                "line":   getattr(element, 'sourceline', None),
                "parent": "",
                "url":      url,
            })

    if not findings:
        masLog(f"{METADATA['name']} check: passed — no aria-required mismatches detected")

    return findings

