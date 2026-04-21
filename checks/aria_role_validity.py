# checks/aria_role_validity.py
# Check 38: Invalid or deprecated ARIA role values.
# WCAG 2.1 Success Criterion 4.1.2 — Name, Role, Value (Level A)
#
# The role attribute communicates the semantic type of an element to
# assistive technologies. When an invalid or deprecated role value is
# used, screen readers either ignore the role entirely or behave
# unpredictably — neither outcome is acceptable.
#
# Common causes of invalid roles:
#   - Typos: role="buttton", role="navigaton"
#   - Made-up roles: role="container", role="wrapper", role="box"
#   - Deprecated roles from older ARIA specs: role="directory"
#   - HTML element names used as roles: role="div", role="span"
#   - Incorrect capitalization: role="Button", role="MAIN"
#
# This check validates role values against the WAI-ARIA 1.2 specification.
# Only the most commonly used roles are included — this is not exhaustive
# but covers the vast majority of real-world usage patterns.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "ARIA Role Validity",
    "wcag":     "4.1.2",
    "level":    "A",
    "severity": config.SEVERITY_HIGH,
    "fix_hint": "Use only valid WAI-ARIA 1.2 role values. Check the ARIA "
                "specification at https://www.w3.org/TR/wai-aria-1.2/ for the "
                "complete list. Common valid roles: alert, alertdialog, application, "
                "article, banner, button, cell, checkbox, columnheader, combobox, "
                "complementary, contentinfo, definition, dialog, directory (deprecated), "
                "document, feed, figure, form, grid, gridcell, group, heading, img, "
                "link, list, listbox, listitem, log, main, marquee, math, menu, "
                "menubar, menuitem, menuitemcheckbox, menuitemradio, navigation, "
                "none, note, option, presentation, progressbar, radio, radiogroup, "
                "region, row, rowgroup, rowheader, scrollbar, search, searchbox, "
                "separator, slider, spinbutton, status, switch, tab, table, tablist, "
                "tabpanel, term, textbox, timer, toolbar, tooltip, tree, treegrid, treeitem.",
}

# Valid WAI-ARIA 1.2 role values.
# Includes both abstract roles (rarely used directly) and concrete roles.
VALID_ROLES = {
    # Landmark roles
    "banner", "complementary", "contentinfo", "form", "main",
    "navigation", "region", "search",
    # Widget roles
    "alert", "alertdialog", "button", "checkbox", "combobox",
    "dialog", "feed", "gridcell", "link", "listbox", "log",
    "marquee", "menuitem", "menuitemcheckbox", "menuitemradio",
    "option", "progressbar", "radio", "scrollbar", "searchbox",
    "separator", "slider", "spinbutton", "status", "switch",
    "tab", "tabpanel", "textbox", "timer", "tooltip", "treeitem",
    # Document structure roles
    "application", "article", "cell", "columnheader", "definition",
    "directory", "document", "figure", "group", "heading", "img",
    "list", "listitem", "math", "none", "note", "presentation",
    "row", "rowgroup", "rowheader", "table", "term", "toolbar",
    # Composite widget roles
    "grid", "menu", "menubar", "radiogroup", "tablist", "tree",
    "treegrid",
    # Generic (HTML5 mapping)
    "generic",
    # Window roles
    "window",
}

# Deprecated roles — still valid but should be noted.
DEPRECATED_ROLES = {"directory"}


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Check all role attributes for valid WAI-ARIA 1.2 values.

    role can contain multiple space-separated values (role chaining).
    Each value in the list is checked individually.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding per invalid or deprecated role value.
    """

    masLog(f"Running check: {METADATA['name']}")

    findings = []

    for element in soup.find_all(role=True):
        role_attr = element.get("role", "").strip()
        if not role_attr:
            continue

        # role can be a space-separated list of fallback roles.
        role_values = role_attr.split()

        for role_val in role_values:
            role_lower = role_val.lower()

            if role_lower in VALID_ROLES:
                if role_lower in DEPRECATED_ROLES:
                    # Deprecated but valid — lower severity informational finding.
                    el_id  = element.get("id", "")
                    el_ref = f'id="{el_id}"' if el_id else f"<{element.name}>"

                    masLog(
                        f"{METADATA['name']} check: role=\"{role_val}\" is deprecated",
                        level="warning"
                    )

                    findings.append({
                        "check":    METADATA["name"],
                        "wcag":     METADATA["wcag"],
                        "level":    METADATA["level"],
                        "severity": config.SEVERITY_LOW,
                        "message":  f"role=\"{role_val}\" is deprecated in WAI-ARIA 1.2. "
                                    f"It may still work but should be replaced with a "
                                    f"current role value. {el_ref}",
                        "element":  str(element)[:120],
                        "fix_hint": METADATA["fix_hint"],
                        "line":   getattr(element, 'sourceline', None),
                        "parent": "",
                        "url":      url,
                    })
                continue

            # Invalid role.
            el_id    = element.get("id", "")
            el_class = " ".join(element.get("class", []))
            el_ref   = (
                f'id="{el_id}"' if el_id
                else f'class="{el_class}"' if el_class
                else f"<{element.name}>"
            )

            masLog(
                f"{METADATA['name']} check: role=\"{role_val}\" on {el_ref} is invalid",
                level="warning"
            )

            findings.append({
                "check":    METADATA["name"],
                "wcag":     METADATA["wcag"],
                "level":    METADATA["level"],
                "severity": METADATA["severity"],
                "message":  f"role=\"{role_val}\" is not a valid WAI-ARIA 1.2 role. "
                            f"Screen readers may ignore this role or behave unpredictably. "
                            f"{el_ref}",
                "element":  str(element)[:120],
                "fix_hint": METADATA["fix_hint"],
                "line":   getattr(element, 'sourceline', None),
                "parent": "",
                "url":      url,
            })

    if not findings:
        masLog(f"{METADATA['name']} check: passed — all role values are valid")

    return findings

