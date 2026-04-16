# checks/svg_accessibility.py
# Check 22: Inline SVG elements missing accessibility attributes.
# WCAG 2.1 Success Criterion 1.1.1 — Non-text Content (Level A)
#
# Inline SVGs are vector graphics embedded directly in HTML. Unlike <img>
# elements, inline SVGs are not automatically treated as images by screen
# readers. Without explicit ARIA attributes, screen readers either ignore
# the SVG entirely or read out all the raw path and coordinate data inside
# it — neither outcome is acceptable for meaningful graphics.
#
# For informational SVGs (icons, logos, charts, illustrations):
#   - role="img" tells screen readers to treat it as an image
#   - A <title> element or aria-label provides the accessible name
#   - aria-labelledby pointing to the <title> connects the two
#
# For decorative SVGs:
#   - aria-hidden="true" removes the SVG from the accessibility tree
#   - No title or label is needed
#
# This check flags inline SVGs that have neither the informational
# pattern (role="img" + label) nor the decorative pattern (aria-hidden).

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "SVG Accessibility Check",
    "wcag":     "1.1.1",
    "level":    "A",
    "severity": config.SEVERITY_HIGH,
    "fix_hint": "For informational SVGs: add role=\"img\" and either a <title> "
                "element as the first child or an aria-label attribute. "
                "Example: <svg role=\"img\" aria-label=\"MAS logo\">...</svg>. "
                "For the best screen reader support, use both: "
                "<svg role=\"img\" aria-labelledby=\"svg-title\">"
                "<title id=\"svg-title\">MAS logo</title>...</svg>. "
                "For decorative SVGs that convey no information: "
                "add aria-hidden=\"true\" to remove them from the accessibility tree.",
}


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Check inline <svg> elements for accessibility attributes.

    An SVG passes if it has either:
      (a) Informational pattern: role="img" AND (aria-label OR <title> child)
      (b) Decorative pattern: aria-hidden="true"

    Any SVG that has neither pattern is flagged.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding per inline SVG missing accessibility attributes.
    """

    masLog(f"Running check: {METADATA['name']}")

    findings = []

    svgs = soup.find_all("svg")

    if not svgs:
        masLog(f"{METADATA['name']} check: passed — no inline <svg> elements found")
        return []

    for svg in svgs:
        aria_hidden = svg.get("aria-hidden", "").strip().lower()
        role        = svg.get("role", "").strip().lower()
        aria_label  = svg.get("aria-label", "").strip()
        aria_labelledby = svg.get("aria-labelledby", "").strip()
        title_tag   = svg.find("title")
        has_title   = title_tag is not None and title_tag.get_text(strip=True)

        # Decorative pattern — aria-hidden removes from accessibility tree.
        if aria_hidden == "true":
            continue

        # Informational pattern — role=img with a label source.
        if role == "img" and (aria_label or aria_labelledby or has_title):
            continue

        # Build issue description.
        missing = []
        if role != "img":
            missing.append('role="img"')
        if not aria_label and not aria_labelledby and not has_title:
            missing.append("accessible name (aria-label, aria-labelledby, or <title>)")

        issue = " and ".join(missing) if missing else "accessibility attributes"

        # Build element identifier.
        svg_id    = svg.get("id", "")
        svg_class = " ".join(svg.get("class", []))
        el_ref    = (
            f'id="{svg_id}"' if svg_id
            else f'class="{svg_class}"' if svg_class
            else "[no identifier]"
        )

        masLog(
            f"{METADATA['name']} check: <svg> {el_ref} missing {issue}",
            level="warning"
        )

        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  f"<svg> is missing {issue}. Without these attributes, "
                        f"screen readers may ignore the graphic or read raw path "
                        f"data. If this SVG conveys information, add role=\"img\" "
                        f"and an accessible name. If decorative, add "
                        f"aria-hidden=\"true\". {el_ref}",
            "element":  str(svg)[:120],
            "fix_hint": METADATA["fix_hint"],
            "line":   getattr(svg, 'sourceline', None),
            "parent": "",
            "url":      url,
        })

    if not findings:
        masLog(f"{METADATA['name']} check: passed — all inline SVGs have accessibility attributes")

    return findings

