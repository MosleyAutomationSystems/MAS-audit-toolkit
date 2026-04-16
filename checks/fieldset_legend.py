# checks/fieldset_legend.py
# Check 24: Grouped radio/checkbox inputs missing fieldset and legend.
# WCAG 2.1 Success Criterion 1.3.1 — Info and Relationships (Level A)
#
# When multiple radio buttons or checkboxes are grouped together as a
# set of related choices, the group needs a programmatic label that
# describes what the choices are for. Without this, screen readers
# announce each individual option but users have no context for what
# question is being answered.
#
# The correct pattern is to wrap the group in a <fieldset> element
# and provide a <legend> as its first child. The legend becomes the
# group label that screen readers read before each option in the group.
#
# Example:
#   <fieldset>
#     <legend>Preferred contact method</legend>
#     <input type="radio" name="contact" id="email"> <label for="email">Email</label>
#     <input type="radio" name="contact" id="phone"> <label for="phone">Phone</label>
#   </fieldset>
#
# This check detects groups of radio buttons (same name attribute) and
# standalone checkboxes that are not inside a fieldset with a legend.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "Fieldset/Legend Check",
    "wcag":     "1.3.1",
    "level":    "A",
    "severity": config.SEVERITY_HIGH,
    "fix_hint": "Wrap groups of radio buttons or checkboxes in a <fieldset> "
                "element with a <legend> as its first child. The legend should "
                "describe the purpose of the group. Example: "
                "<fieldset><legend>Preferred contact method</legend>"
                "<input type=\"radio\" name=\"contact\" id=\"r1\">"
                "<label for=\"r1\">Email</label></fieldset>. "
                "A single checkbox that stands alone (e.g. 'I agree to terms') "
                "does not require a fieldset — a standard label is sufficient.",
}


def _get_ancestor_fieldset(element) -> object | None:
    """
    Walk up the DOM tree to find a <fieldset> ancestor.

    Returns the fieldset element if found, or None.

    Parameters:
        element: A BeautifulSoup tag element.

    Returns:
        BeautifulSoup tag | None: The nearest fieldset ancestor, or None.
    """
    parent = element.parent
    while parent and parent.name != "[document]":
        if parent.name == "fieldset":
            return parent
        parent = parent.parent
    return None


def _fieldset_has_legend(fieldset) -> bool:
    """
    Check whether a fieldset has a non-empty legend as a direct child.

    Parameters:
        fieldset: A BeautifulSoup fieldset element.

    Returns:
        bool: True if a non-empty legend exists, False otherwise.
    """
    legend = fieldset.find("legend")
    return legend is not None and bool(legend.get_text(strip=True))


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Check grouped radio/checkbox inputs for fieldset and legend.

    Logic:
      1. Find all radio button groups (inputs sharing the same name attribute).
         Groups with 2+ members that are not in a fieldset+legend are flagged.
      2. Find all checkboxes not in a fieldset+legend.
         Standalone checkboxes (only one with a given name) are exempt.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding per ungrouped radio group or ungrouped checkbox group.
    """

    masLog(f"Running check: {METADATA['name']}")

    findings = []
    reported_names = set()

    # ── Radio button groups ──────────────────────────────────────────────────
    # Group all radio inputs by their name attribute.
    radio_groups: dict[str, list] = {}
    for radio in soup.find_all("input", attrs={"type": "radio"}):
        name = radio.get("name", "").strip()
        if not name:
            name = "[no name]"
        radio_groups.setdefault(name, []).append(radio)

    for group_name, radios in radio_groups.items():
        if len(radios) < 2:
            continue  # Single radio is not a group — skip.

        if group_name in reported_names:
            continue

        # Check if any radio in the group is inside a fieldset with a legend.
        fieldset = _get_ancestor_fieldset(radios[0])
        if fieldset and _fieldset_has_legend(fieldset):
            continue

        reported_names.add(group_name)

        masLog(
            f"{METADATA['name']} check: radio group name=\"{group_name}\" "
            f"({len(radios)} inputs) missing fieldset+legend",
            level="warning"
        )

        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  f"Radio button group name=\"{group_name}\" has {len(radios)} "
                        f"options but is not wrapped in a <fieldset> with a <legend>. "
                        f"Screen readers cannot communicate what question this group answers.",
            "element":  str(radios[0])[:120],
            "fix_hint": METADATA["fix_hint"],
            "line":   None,
            "parent": "",
            "url":      url,
        })

    # ── Checkbox groups ──────────────────────────────────────────────────────
    # Group checkboxes by name. Only flag groups with 2+ members.
    checkbox_groups: dict[str, list] = {}
    for checkbox in soup.find_all("input", attrs={"type": "checkbox"}):
        name = checkbox.get("name", "").strip()
        if not name:
            name = "[no name]"
        checkbox_groups.setdefault(name, []).append(checkbox)

    for group_name, checkboxes in checkbox_groups.items():
        if len(checkboxes) < 2:
            continue  # Single checkbox doesn't need a fieldset.

        if group_name in reported_names:
            continue

        fieldset = _get_ancestor_fieldset(checkboxes[0])
        if fieldset and _fieldset_has_legend(fieldset):
            continue

        reported_names.add(group_name)

        masLog(
            f"{METADATA['name']} check: checkbox group name=\"{group_name}\" "
            f"({len(checkboxes)} inputs) missing fieldset+legend",
            level="warning"
        )

        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  f"Checkbox group name=\"{group_name}\" has {len(checkboxes)} "
                        f"options but is not wrapped in a <fieldset> with a <legend>. "
                        f"Screen readers cannot communicate what this group of options represents.",
            "element":  str(checkboxes[0])[:120],
            "fix_hint": METADATA["fix_hint"],
            "line":   None,
            "parent": "",
            "url":      url,
        })

    if not findings:
        masLog(f"{METADATA['name']} check: passed — all grouped inputs have fieldset+legend")

    return findings

