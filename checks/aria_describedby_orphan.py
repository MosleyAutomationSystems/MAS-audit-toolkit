# checks/aria_describedby_orphan.py
# Check 37: aria-describedby pointing to non-existent IDs.
# WCAG 2.1 Success Criterion 4.1.2 — Name, Role, Value (Level A)
#
# The aria-describedby attribute associates an element with one or more
# descriptive elements identified by their IDs. Screen readers read the
# referenced element's text as additional context after the element's
# primary label.
#
# Common uses:
#   - Form field hints: <input aria-describedby="hint-1"> with <p id="hint-1">
#   - Error messages: <input aria-describedby="error-1"> with <span id="error-1">
#   - Tooltips: <button aria-describedby="tooltip-1"> with <div id="tooltip-1">
#
# When aria-describedby references an ID that doesn't exist on the page,
# screen readers silently ignore it — the description is simply missing.
# This is a broken ARIA reference that degrades the accessible experience
# without any visible error.
#
# aria-describedby can reference multiple IDs separated by spaces.
# Each ID in the list is checked individually.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "aria-describedby Orphan Check",
    "wcag":     "4.1.2",
    "level":    "A",
    "severity": config.SEVERITY_HIGH,
    "fix_hint": "Ensure every ID referenced in aria-describedby exists on the page. "
                "Check for: (1) Typos in the ID reference or the target element's id. "
                "(2) The target element being conditionally rendered and absent from "
                "the current page state. (3) IDs that were renamed during a CMS update. "
                "Fix: verify the id attribute on the target element matches the "
                "aria-describedby value exactly, including case sensitivity.",
}


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Check all aria-describedby attributes for orphaned ID references.

    Collects all IDs on the page first, then checks each aria-describedby
    value against that set. Each referenced ID that does not exist is flagged
    as a separate finding.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding per orphaned aria-describedby ID reference.
    """

    masLog(f"Running check: {METADATA['name']}")

    # Build a set of all IDs on the page for fast lookup.
    all_ids = {
        tag.get("id")
        for tag in soup.find_all(id=True)
        if tag.get("id", "").strip()
    }

    findings = []

    for element in soup.find_all(attrs={"aria-describedby": True}):
        aria_describedby = element.get("aria-describedby", "").strip()
        if not aria_describedby:
            continue

        # aria-describedby can reference multiple space-separated IDs.
        referenced_ids = aria_describedby.split()

        for ref_id in referenced_ids:
            if ref_id in all_ids:
                continue

            # Build element identifier.
            el_id   = element.get("id", "")
            el_name = element.get("name", "")
            el_text = element.get_text(strip=True)[:30]
            el_ref  = (
                f'id="{el_id}"' if el_id
                else f'name="{el_name}"' if el_name
                else f'text="{el_text}"' if el_text
                else f"<{element.name}>"
            )

            masLog(
                f"{METADATA['name']} check: aria-describedby=\"{ref_id}\" "
                f"on {el_ref} — target ID not found on page",
                level="warning"
            )

            findings.append({
                "check":    METADATA["name"],
                "wcag":     METADATA["wcag"],
                "level":    METADATA["level"],
                "severity": METADATA["severity"],
                "message":  f"aria-describedby references id=\"{ref_id}\" but no "
                            f"element with that ID exists on the page. "
                            f"Screen readers will silently skip this description — "
                            f"users lose access to the associated help text or error message. "
                            f"Element: {el_ref}",
                "element":  str(element)[:120],
                "fix_hint": METADATA["fix_hint"],
                "line":   getattr(element, 'sourceline', None),
                "parent": "",
                "url":      url,
            })

    if not findings:
        masLog(f"{METADATA['name']} check: passed — all aria-describedby references are valid")

    return findings

