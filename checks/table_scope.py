# checks/table_scope.py
# Check 18: Table header elements missing scope attribute.
# WCAG 2.1 Success Criterion 1.3.1 — Info and Relationships (Level A)
#
# The scope attribute on <th> elements explicitly associates a header cell
# with the row or column it describes. Without scope, screen readers cannot
# reliably communicate the relationship between header and data cells,
# making tabular data difficult or impossible to understand for blind users.
#
# Valid scope values:
#   col     — header applies to all cells in the column below
#   row     — header applies to all cells in the row to the right
#   colgroup — header applies to a group of columns
#   rowgroup — header applies to a group of rows

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "Table Scope Attributes",
    "wcag":     "1.3.1",
    "level":    "A",
    "severity": config.SEVERITY_HIGH,
    "fix_hint": "Add a scope attribute to every <th> element. Use scope=\"col\" "
                "for column headers and scope=\"row\" for row headers. "
                "Example: <th scope=\"col\">Name</th> or <th scope=\"row\">Total</th>. "
                "For complex tables with merged cells, use scope=\"colgroup\" "
                "or scope=\"rowgroup\" as appropriate.",
}

# Valid values for the scope attribute per HTML specification.
VALID_SCOPE_VALUES = {"col", "row", "colgroup", "rowgroup"}


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Check all <th> elements for a valid scope attribute.

    Flags any <th> that is missing the scope attribute entirely,
    or has an empty or invalid scope value.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding per <th> element with a missing or invalid scope.
    """

    masLog(f"Running check: {METADATA['name']}")

    findings = []

    th_elements = soup.find_all("th")

    if not th_elements:
        masLog(f"{METADATA['name']} check: passed — no <th> elements found")
        return []

    for th in th_elements:
        scope = th.get("scope", "").strip().lower()

        if scope in VALID_SCOPE_VALUES:
            continue

        # Build a readable identifier for the finding message.
        th_text  = th.get_text(strip=True)[:40]
        th_id    = th.get("id", "")
        el_ref   = (
            f'id="{th_id}"' if th_id
            else f'text="{th_text}"' if th_text
            else "[no identifier]"
        )

        if not scope:
            issue = "missing scope attribute"
            message = (
                f"<th> element is missing the scope attribute — "
                f"screen readers cannot reliably associate this header "
                f"with its data cells. {el_ref}"
            )
        else:
            issue = f"invalid scope value: \"{scope}\""
            message = (
                f"<th> element has an invalid scope value \"{scope}\" — "
                f"valid values are: col, row, colgroup, rowgroup. {el_ref}"
            )

        masLog(
            f"{METADATA['name']} check: <th> {el_ref} has {issue}",
            level="warning"
        )

        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  message,
            "element":  str(th)[:120],
            "fix_hint": METADATA["fix_hint"],
            "line":   getattr(th, 'sourceline', None),
            "parent": "",
            "url":      url,
        })

    if not findings:
        masLog(f"{METADATA['name']} check: passed — all <th> elements have valid scope")

    return findings

