# checks/autocomplete_attr.py
# Check 25: Personal data inputs missing autocomplete attribute.
# WCAG 2.1 Success Criterion 1.3.5 — Identify Input Purpose (Level AA)
#
# The autocomplete attribute tells browsers and password managers the
# semantic purpose of an input field. This allows browsers to pre-fill
# personal information automatically, which dramatically reduces the
# effort required from users with cognitive disabilities, motor
# impairments, or memory difficulties.
#
# Without autocomplete, users must manually type their name, email,
# address, phone number, and payment details on every form — a
# significant barrier for users who struggle with repetitive data entry.
#
# This check inspects inputs whose type or name attribute suggests they
# collect personal data, and flags those missing a valid autocomplete value.
#
# WCAG 1.3.5 applies to inputs that collect information about the user.
# It does not apply to search fields, OTP codes, or CAPTCHA inputs.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "Autocomplete Attribute",
    "wcag":     "1.3.5",
    "level":    "AA",
    "severity": config.SEVERITY_MEDIUM,
    "fix_hint": "Add an autocomplete attribute to inputs that collect personal "
                "information. Use the appropriate token: name, email, tel, "
                "street-address, address-line1, address-line2, address-level1, "
                "address-level2, postal-code, country, bday, cc-name, cc-number, "
                "cc-exp, cc-csc, new-password, current-password, username. "
                "Example: <input type=\"email\" autocomplete=\"email\">. "
                "Use autocomplete=\"off\" only when pre-filling would create a "
                "security risk (e.g. OTP, CAPTCHA).",
}

# Input name/id patterns that suggest personal data collection.
# Matched case-insensitively against the name and id attributes.
PERSONAL_DATA_PATTERNS = [
    "name", "fname", "lname", "firstname", "lastname", "fullname",
    "email", "mail",
    "phone", "tel", "mobile", "cellphone",
    "address", "addr", "street", "city", "state", "zip", "postal", "country",
    "birthday", "bday", "dob",
    "username", "user_name", "login",
    "password", "passwd", "pwd",
    "card", "cc", "credit", "cardnumber", "cvv", "cvc", "expiry", "expiration",
]

# Input types that inherently suggest personal data.
PERSONAL_DATA_TYPES = {"email", "tel", "password"}

# Valid autocomplete token values per HTML spec.
# This is not exhaustive — we check for non-empty, non-off values.
INVALID_AUTOCOMPLETE = {"", "off", "false", "none"}


def _is_personal_input(input_tag) -> bool:
    """
    Determine whether an input likely collects personal data.

    Checks the type attribute first, then name and id patterns.

    Parameters:
        input_tag: A BeautifulSoup input element.

    Returns:
        bool: True if the input likely collects personal data.
    """
    input_type = input_tag.get("type", "text").strip().lower()

    if input_type in PERSONAL_DATA_TYPES:
        return True

    # Skip inputs that clearly don't collect personal data.
    if input_type in {"submit", "button", "reset", "image", "file",
                      "hidden", "checkbox", "radio", "range", "color"}:
        return False

    name = input_tag.get("name", "").strip().lower()
    id_  = input_tag.get("id", "").strip().lower()
    combined = name + " " + id_

    return any(pattern in combined for pattern in PERSONAL_DATA_PATTERNS)


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Check inputs that collect personal data for a valid autocomplete attribute.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One finding per personal data input missing autocomplete.
    """

    masLog(f"Running check: {METADATA['name']}")

    findings = []

    for input_tag in soup.find_all("input"):
        if not _is_personal_input(input_tag):
            continue

        autocomplete = input_tag.get("autocomplete", "").strip().lower()

        if autocomplete and autocomplete not in INVALID_AUTOCOMPLETE:
            continue

        # Build element identifier.
        name     = input_tag.get("name", "[no name]")
        id_      = input_tag.get("id", "")
        inp_type = input_tag.get("type", "text")
        el_ref   = (
            f'id="{id_}"' if id_
            else f'name="{name}"'
        )

        if not autocomplete:
            issue = "missing autocomplete attribute"
        else:
            issue = f"autocomplete=\"{autocomplete}\" disables autofill"

        masLog(
            f"{METADATA['name']} check: <input type=\"{inp_type}\"> {el_ref} has {issue}",
            level="warning"
        )

        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  f"<input type=\"{inp_type}\"> collecting personal data has {issue}. "
                        f"Users with cognitive disabilities or motor impairments rely on "
                        f"browser autofill to complete forms. {el_ref}",
            "element":  str(input_tag)[:120],
            "fix_hint": METADATA["fix_hint"],
            "line":   getattr(input_tag, 'sourceline', None),
            "parent": "",
            "url":      url,
        })

    if not findings:
        masLog(f"{METADATA['name']} check: passed — all personal data inputs have valid autocomplete")

    return findings

