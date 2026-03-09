# checks/tabindex.py
# Check 6: tabindex values greater than 0.
# WCAG 2.1 Success Criterion 2.4.3 — Focus Order (Level A)
# tabindex="1" or higher forces an unnatural tab order by overriding
# the document's natural DOM sequence. Screen reader and keyboard users
# encounter controls in the wrong order. Only tabindex="0" (adds to
# natural order) and tabindex="-1" (removes from tab order) are safe.

from bs4 import BeautifulSoup
from utils.logger import masLog

def check_tabindex(soup: BeautifulSoup) -> list:
    """
    Find all elements with a tabindex value greater than 0.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.

    Returns:
        list: A list of finding dictionaries for each violating element.
    """

    masLog("Running check: tabindex values")

    findings = []

    # Find every element in the document that has a tabindex attribute.
    # We do not limit by tag name — tabindex can appear on any element.
    elements = soup.find_all(attrs={"tabindex": True})

    masLog(f"Found {len(elements)} element(s) with tabindex attribute")

    for el in elements:
        raw = el.get("tabindex", "").strip()

        try:
            # Convert to integer. Non-numeric values (e.g. tabindex="auto")
            # are invalid HTML — we skip rather than crash.
            value = int(raw)
        except ValueError:
            continue

        # tabindex > 0 is the failure condition.
        # tabindex="0"  — safe, adds element to natural tab order.
        # tabindex="-1" — safe, removes from tab order (used for JS focus management).
        # tabindex="1"+ — unsafe, creates a separate tab sequence that
        #                  overrides DOM order for ALL positive-index elements.
        if value > 0:
            # el.name gives the tag name. el.get() gives attribute values.
            tag  = el.name
            id_  = el.get("id",    "[no id]")
            text = el.get_text(strip=True)[:40] or "[no text]"

            findings.append({
                "check":    "Keyboard Trap / Focus Order",
                "wcag":     "2.4.3",
                "level":    "A",
                "severity": "critical",
                "message":  (
                    f'<{tag}> has tabindex="{value}" — '
                    f'positive tabindex disrupts natural focus order. '
                    f'id="{id_}", text="{text}"'
                )
            })

    if findings:
        masLog(f"Tabindex check: {len(findings)} issue(s) found", level="warning")
    else:
        masLog("Tabindex check: passed — no positive tabindex values found")

    return findings
