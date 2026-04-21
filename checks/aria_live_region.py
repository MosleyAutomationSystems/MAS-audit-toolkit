# checks/aria_live.py
# Check 49: aria-live Region Detection.
# Flags dynamic content areas missing aria-live regions.
# Static analysis only — detects structural signals of dynamic content
# (role=alert/status, aria-atomic without aria-live, and common
# dynamic-region class/id naming patterns) rather than runtime DOM changes.
# WCAG 4.1.3 — Status Messages — Level AA

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "aria-live Region Detection",
    "wcag":     "4.1.3",
    "level":    "AA",
    "severity": config.SEVERITY_HIGH,
    "fix_hint": (
        "Add aria-live='polite' to regions that update dynamically without "
        "a page reload. Use aria-live='assertive' only for urgent alerts. "
        "role='alert' implies aria-live='assertive' — use sparingly."
    ),
}

# role values that imply dynamic content and require aria-live if not already set.
DYNAMIC_ROLES = {"alert", "status", "log", "marquee", "timer", "progressbar"}

# Class and ID keyword fragments that signal a developer-intended dynamic region.
DYNAMIC_KEYWORDS = {
    "alert", "alerts", "status", "notification", "notifications",
    "toast", "toasts", "message", "messages", "error", "errors",
    "success", "warning", "warnings", "live", "announce", "announcer",
    "feedback", "snackbar",
}

VALID_LIVE_VALUES = {"polite", "assertive", "off"}


def _has_aria_live(el) -> bool:
    """Return True if the element has a valid aria-live attribute."""
    return el.get("aria-live", "").strip().lower() in VALID_LIVE_VALUES


def _check_role_without_live(soup, url, findings):
    """
    Flag elements with a dynamic ARIA role but no aria-live attribute.
    role='alert' and role='status' carry implicit live region semantics
    in the spec, but explicit aria-live is more reliably supported across
    assistive technology combinations.
    """
    for el in soup.find_all(True):
        role = el.get("role", "").strip().lower()
        if role not in DYNAMIC_ROLES:
            continue
        if _has_aria_live(el):
            continue
        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": config.SEVERITY_HIGH,
            "message":  (
                f'<{el.name}> has role="{role}" but no aria-live attribute. '
                f'Screen readers may not announce updates to this region. '
                f'id="{el.get("id", "[no id]")}"'
            ),
            "element":  str(el)[:120],
            "fix_hint": (
                f'Add aria-live="polite" to this element, or aria-live="assertive" '
                f'if the content requires immediate interruption of the screen reader.'
            ),
            "line":     getattr(el, "sourceline", None),
            "parent":   "",
            "url":      url,
        })


def _check_aria_atomic_without_live(soup, url, findings):
    """
    Flag elements with aria-atomic but no aria-live.
    aria-atomic controls how updates are read — it has no effect without
    aria-live and signals that the author intended a live region.
    """
    for el in soup.find_all(attrs={"aria-atomic": True}):
        if _has_aria_live(el):
            continue
        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": config.SEVERITY_MEDIUM,
            "message":  (
                f'<{el.name}> has aria-atomic but no aria-live attribute. '
                f'aria-atomic has no effect without aria-live. '
                f'id="{el.get("id", "[no id]")}"'
            ),
            "element":  str(el)[:120],
            "fix_hint": (
                'Add aria-live="polite" alongside aria-atomic. '
                'Without aria-live, aria-atomic is ignored by assistive technologies.'
            ),
            "line":     getattr(el, "sourceline", None),
            "parent":   "",
            "url":      url,
        })


def _check_keyword_regions_without_live(soup, url, findings):
    """
    Flag elements whose id or class contains dynamic-region keywords
    but lack aria-live. These are developer-named regions that are
    structurally intended to receive dynamic updates.
    """
    for el in soup.find_all(True):
        # Skip if already has aria-live or a dynamic role (covered above).
        if _has_aria_live(el):
            continue
        if el.get("role", "").strip().lower() in DYNAMIC_ROLES:
            continue

        el_id      = el.get("id", "").lower()
        el_classes = " ".join(el.get("class", [])).lower()
        combined   = el_id + " " + el_classes

        matched = [kw for kw in DYNAMIC_KEYWORDS if kw in combined]
        if not matched:
            continue

        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": config.SEVERITY_MEDIUM,
            "message":  (
                f'<{el.name}> id="{el.get("id", "[no id]")}" '
                f'class="{" ".join(el.get("class", []))}" — '
                f'naming suggests a dynamic region but aria-live is missing. '
                f'Matched keyword(s): {", ".join(matched)}'
            ),
            "element":  str(el)[:120],
            "fix_hint": (
                'If this element receives dynamic updates, add aria-live="polite". '
                'If it is static content, rename the id/class to avoid false signals.'
            ),
            "line":     getattr(el, "sourceline", None),
            "parent":   "",
            "url":      url,
        })


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Run all aria-live region detection checks.

    Parameters:
        soup (BeautifulSoup): Parsed HTML document.
        url  (str):           Source URL or file path.

    Returns:
        list: All findings from aria-live sub-checks.
    """
    masLog(f"Running check: {METADATA['name']}")

    findings = []

    _check_role_without_live(soup, url, findings)
    _check_aria_atomic_without_live(soup, url, findings)
    _check_keyword_regions_without_live(soup, url, findings)

    if findings:
        masLog(
            f"{METADATA['name']} check: {len(findings)} issue(s) found",
            level="warning"
        )
    else:
        masLog(f"{METADATA['name']} check: passed")

    return findings