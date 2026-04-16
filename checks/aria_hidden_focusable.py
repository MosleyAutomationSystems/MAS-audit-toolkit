# checks/aria_hidden_focusable.py
# Check 35: aria-hidden="true" on elements still in the tab order.
# WCAG 2.1 Success Criterion 4.1.2 — Name, Role, Value (Level A)
#
# aria-hidden="true" removes an element from the accessibility tree —
# screen readers will not announce it. However, if the element or any
# of its descendants are still focusable (via Tab key), keyboard users
# can navigate to an element that screen readers are completely silent
# about. This creates an invisible focus trap:
#
#   - Sighted keyboard users can see focus land on the element
#   - Screen reader users hear nothing — they don't know where focus is
#   - The element cannot be activated meaningfully via keyboard
#
# This is one of the most dangerous ARIA misuses. Common causes:
#   - Decorative icon buttons with aria-hidden on the icon but not the button
#   - Modal overlays that hide the trigger button but leave it focusable
#   - Tab panels that hide inactive panels with aria-hidden but forget tabindex
#   - Visually hidden elements that use aria-hidden instead of display:none
#
# The fix depends on intent:
#   - If the element should be invisible to everyone: add display:none or
#     visibility:hidden (removes from both visual and accessibility tree)
#   - If the element is decorative inside an interactive control: move
#     aria-hidden to the decorative child, not the interactive parent
#   - If the element should be screen-reader-only: use a visually-hidden
#     CSS class, not aria-hidden

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "aria-hidden on Focusable Elements",
    "wcag":     "4.1.2",
    "level":    "A",
    "severity": config.SEVERITY_CRITICAL,
    "fix_hint": "Never place aria-hidden=\"true\" on an element that can receive "
                "keyboard focus. Options: (1) Add tabindex=\"-1\" to remove the "
                "element from the tab order while keeping it in the DOM. "
                "(2) Use display:none or visibility:hidden instead of aria-hidden "
                "to remove the element from both visual and accessibility trees. "
                "(3) If the element contains a focusable child, move aria-hidden "
                "to the decorative descendant only, not the interactive parent.",
}

# Natively focusable elements that are focusable by default without tabindex.
NATIVELY_FOCUSABLE = {"a", "button", "input", "select", "textarea", "details", "summary"}


def _is_focusable(element) -> bool:
    """
    Determine whether an element is keyboard focusable.

    An element is focusable if:
      1. It is a natively focusable tag (a, button, input, etc.) and
         not disabled, OR
      2. It has a tabindex attribute with a value >= 0

    Parameters:
        element: A BeautifulSoup tag element.

    Returns:
        bool: True if the element can receive keyboard focus.
    """
    tag = element.name.lower() if element.name else ""

    # Check for explicit tabindex.
    tabindex = element.get("tabindex", None)
    if tabindex is not None:
        try:
            if int(tabindex) >= 0:
                return True
        except ValueError:
            pass

    # Check natively focusable tags.
    if tag in NATIVELY_FOCUSABLE:
        # Disabled elements are not focusable.
        if element.get("disabled") is not None:
            return False
        # <a> without href is not focusable.
        if tag == "a" and element.get("href") is None:
            return False
        return True

    return False


def _find_focusable_descendants(element) -> list:
    """
    Find all focusable descendants of an element.

    Parameters:
        element: A BeautifulSoup tag element.

    Returns:
        list: All focusable descendant elements.
    """
    focusable = []
    for tag in NATIVELY_FOCUSABLE:
        for descendant in element.find_all(tag):
            if _is_focusable(descendant):
                focusable.append(descendant)
    # Also check descendants with explicit tabindex >= 0.
    for descendant in element.find_all(tabindex=True):
        if descendant not in focusable and _is_focusable(descendant):
            focusable.append(descendant)
    return focusable


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Find elements with aria-hidden="true" that are still keyboard focusable.

    Checks both the element itself and its descendants for focusability.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding per aria-hidden element with focusable content.
    """

    masLog(f"Running check: {METADATA['name']}")

    findings = []
    reported = set()

    for element in soup.find_all(attrs={"aria-hidden": "true"}):
        if id(element) in reported:
            continue

        # Check if the element itself is focusable.
        if _is_focusable(element):
            reported.add(id(element))

            el_id    = element.get("id", "")
            el_class = " ".join(element.get("class", []))
            el_text  = element.get_text(strip=True)[:30]

            # Dedup by class signature — one finding per unique class pattern.
            dedup_key = f"{element.name}::{el_class}" if el_class else f"{element.name}::{el_id}"
            if dedup_key in reported:
                continue
            reported.add(dedup_key)

            el_ref = (
                f'id="{el_id}"' if el_id
                else f'class="{el_class}"' if el_class
                else f'text="{el_text}"' if el_text
                else "[no identifier]"
            )

            # Count how many elements share this class pattern.
            if el_class:
                class_list = element.get("class", [])
                same_class_count = len([
                    e for e in soup.find_all(element.name)
                    if e.get("class", []) == class_list
                    and e.get("aria-hidden") == "true"
                    and _is_focusable(e)
                ])
                count_note = f" ({same_class_count} instance(s) on this page)" if same_class_count > 1 else ""
            else:
                count_note = ""

            masLog(
                f"{METADATA['name']} check: <{element.name}> {el_ref} "
                f"has aria-hidden=true but is focusable",
                level="warning"
            )

            findings.append({
                "check":    METADATA["name"],
                "wcag":     METADATA["wcag"],
                "level":    METADATA["level"],
                "severity": METADATA["severity"],
                "message":  f"<{element.name}> has aria-hidden=\"true\" but is "
                            f"still keyboard focusable. Screen reader users cannot "
                            f"perceive this element while keyboard users can reach it — "
                            f"creating an invisible focus trap. {el_ref}{count_note}",
                "element":  str(element)[:120],
                "fix_hint": METADATA["fix_hint"],
                "line":   getattr(element, 'sourceline', None),
                "parent": "",
                "url":      url,
            })
            continue

# Check for focusable descendants — one finding per container, not per descendant.
        focusable_descendants = _find_focusable_descendants(element)
        if not focusable_descendants:
            continue

        container_id = id(element)
        if container_id in reported:
            continue
        reported.add(container_id)

        parent_id  = element.get("id", "")
        parent_ref = f'id="{parent_id}"' if parent_id else f"<{element.name}>"
        count      = len(focusable_descendants)

        # Sample up to 3 focusable descendants for the message.
        samples = []
        for d in focusable_descendants[:3]:
            d_text = d.get_text(strip=True)[:20]
            samples.append(f'<{d.name}> "{d_text}"' if d_text else f"<{d.name}>")
        sample_str = ", ".join(samples)
        if count > 3:
            sample_str += f" (+{count - 3} more)"

        masLog(
            f"{METADATA['name']} check: aria-hidden {parent_ref} "
            f"contains {count} focusable descendant(s)",
            level="warning"
        )

        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  f"aria-hidden=\"true\" container ({parent_ref}) has "
                        f"{count} keyboard-focusable descendant(s) — screen reader "
                        f"users hear nothing when focus lands on any of them. "
                        f"Focusable elements: {sample_str}.",
            "element":  str(element)[:120],
            "fix_hint": METADATA["fix_hint"],
            "line":   getattr(element, 'sourceline', None),
            "parent": "",
            "url":      url,
        })

    if not findings:
        masLog(f"{METADATA['name']} check: passed — no aria-hidden elements with focusable content")

    return findings

