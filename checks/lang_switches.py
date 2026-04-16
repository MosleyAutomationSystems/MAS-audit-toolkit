# checks/lang_switches.py
# Check 29: Multi-language content missing lang attribute on element.
# WCAG 2.1 Success Criterion 3.1.2 — Language of Parts (Level AA)
#
# When a page contains text in a language different from the page's
# primary language (set on the <html> element), that passage must have
# a lang attribute on the element containing it. Without this, screen
# readers use the wrong language engine to pronounce the text, producing
# unintelligible output for blind users.
#
# Examples of content that needs lang attributes:
#   - A French phrase on an English page
#   - A Spanish navigation item on an English site
#   - A Japanese product name in an English description
#   - A quote in another language
#
# This check cannot detect which language text is written in — that
# requires natural language processing beyond static HTML analysis.
# Instead, it detects common HTML patterns that strongly suggest
# intentional language switching:
#   1. Elements with a lang attribute already set to a different value
#      than the page's html[lang] — validates the value is non-empty
#   2. Elements containing common language-switch markers:
#      <span lang="">, <p lang="">, <blockquote lang="">
#   3. Elements with class names suggesting language context
#
# This is a heuristic check. It flags patterns that indicate language
# switching is intended but the lang attribute is missing or empty.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "Lang on Language Switches",
    "wcag":     "3.1.2",
    "level":    "AA",
    "severity": config.SEVERITY_MEDIUM,
    "fix_hint": "Add a lang attribute to any element containing text in a "
                "language different from the page's primary language. Use a "
                "valid BCP 47 language tag. Examples: lang=\"fr\" for French, "
                "lang=\"es\" for Spanish, lang=\"ja\" for Japanese, "
                "lang=\"de\" for German, lang=\"zh\" for Chinese. "
                "The lang attribute can be placed on any HTML element: "
                "<span lang=\"fr\">Bonjour</span> or "
                "<blockquote lang=\"es\">Hola mundo</blockquote>.",
}

# Tags commonly used to wrap language-switched content.
LANGUAGE_SWITCH_TAGS = {"span", "p", "div", "blockquote", "q", "cite",
                        "section", "article", "aside", "li", "td", "th"}

# Class name patterns that suggest intentional language context.
LANGUAGE_CLASS_PATTERNS = [
    "lang-", "language-", "locale-", "i18n-", "l10n-",
    "-lang", "-language", "-locale",
]


def _has_language_class(element) -> bool:
    """
    Check if an element has a class name suggesting language context.

    Parameters:
        element: A BeautifulSoup tag element.

    Returns:
        bool: True if any class name matches a language pattern.
    """
    classes = element.get("class", [])
    for cls in classes:
        cls_lower = cls.lower()
        if any(pattern in cls_lower for pattern in LANGUAGE_CLASS_PATTERNS):
            return True
    return False


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Detect elements with empty lang attributes or language-class patterns
    that suggest multi-language content without proper lang markup.

    Two detection patterns:
      1. Elements with lang="" (empty lang attribute) — the developer
         intended to mark a language switch but left the value empty.
      2. Elements with class names suggesting language context but no
         lang attribute — likely language-switch wrappers missing the attribute.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding per element with a missing or empty lang on a
              likely language-switch element.
    """

    masLog(f"Running check: {METADATA['name']}")

    findings = []
    seen_elements = set()

    # Pattern 1: Elements with lang="" (empty lang attribute).
    for tag_name in LANGUAGE_SWITCH_TAGS:
        for element in soup.find_all(tag_name):
            if id(element) in seen_elements:
                continue

            lang_val = element.get("lang", None)

            # Only flag elements that have lang attribute but it's empty.
            if lang_val is None:
                continue
            if lang_val.strip():
                continue  # Non-empty lang — valid, skip.

            seen_elements.add(id(element))
            text_preview = element.get_text(strip=True)[:40]

            masLog(
                f"{METADATA['name']} check: <{tag_name}> has empty lang attribute",
                level="warning"
            )

            findings.append({
                "check":    METADATA["name"],
                "wcag":     METADATA["wcag"],
                "level":    METADATA["level"],
                "severity": METADATA["severity"],
                "message":  f"<{tag_name}> has an empty lang=\"\" attribute. "
                            f"This indicates a language switch was intended but "
                            f"the language code was not set. Screen readers will "
                            f"use the wrong voice/pronunciation engine for this content. "
                            f"Text preview: \"{text_preview}\"",
                "element":  str(element)[:120],
                "fix_hint": METADATA["fix_hint"],
                "line":   getattr(element, 'sourceline', None),
                "parent": "",
                "url":      url,
            })

    # Pattern 2: Elements with language-suggesting class names but no lang attribute.
    for tag_name in LANGUAGE_SWITCH_TAGS:
        for element in soup.find_all(tag_name):
            if id(element) in seen_elements:
                continue
            if element.get("lang") is not None:
                continue  # Already has a lang attribute — skip.
            if not _has_language_class(element):
                continue

            seen_elements.add(id(element))
            classes = " ".join(element.get("class", []))
            text_preview = element.get_text(strip=True)[:40]

            masLog(
                f"{METADATA['name']} check: <{tag_name} class=\"{classes}\"> "
                f"suggests language switch but has no lang attribute",
                level="warning"
            )

            findings.append({
                "check":    METADATA["name"],
                "wcag":     METADATA["wcag"],
                "level":    METADATA["level"],
                "severity": METADATA["severity"],
                "message":  f"<{tag_name} class=\"{classes}\"> appears to mark "
                            f"a language switch (class name pattern detected) but "
                            f"has no lang attribute. If this content is in a different "
                            f"language, add the appropriate lang attribute. "
                            f"Text preview: \"{text_preview}\"",
                "element":  str(element)[:120],
                "fix_hint": METADATA["fix_hint"],
                "line":   getattr(element, 'sourceline', None),
                "parent": "",
                "url":      url,
            })

    if not findings:
        masLog(f"{METADATA['name']} check: passed — no missing lang on language switches detected")

    return findings

