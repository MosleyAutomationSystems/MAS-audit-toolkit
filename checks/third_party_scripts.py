# checks/third_party_scripts.py
# Check 44: Third-party analytics and ad scripts as supply-chain risk.
# Mosley Standard — Security/Operational (MS)
#
# Third-party scripts loaded from external domains represent a supply-chain
# risk. If the external domain is compromised, the malicious script runs
# with full access to the page — including form data, cookies, and user
# interactions. This is known as a supply-chain or Magecart-style attack.
#
# From an accessibility standpoint, third-party scripts can:
#   - Inject inaccessible overlays or widgets
#   - Override keyboard focus management
#   - Add unlabeled interactive elements
#   - Slow page load times, affecting users on low bandwidth
#
# This check is informational (INFO) — it does not flag third-party scripts
# as failures. It surfaces them for awareness so auditors can:
#   1. Verify each script is intentional
#   2. Confirm Subresource Integrity (SRI) is implemented where possible
#   3. Review the Content Security Policy to ensure scripts are allowlisted
#
# Common third-party script domains are checked. Unknown external scripts
# are also flagged generically.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name":     "Third-Party Script Risk",
    "wcag":     "MS",
    "level":    "MS",
    "severity": config.SEVERITY_INFO,
    "fix_hint": "Review all third-party scripts for necessity and security. "
                "For each script: (1) Confirm it is intentional and still needed. "
                "(2) Add Subresource Integrity (SRI) where the vendor supports it: "
                "integrity=\"sha384-...\" crossorigin=\"anonymous\". "
                "(3) Add the domain to your Content Security Policy script-src. "
                "(4) Consider self-hosting critical scripts to eliminate the "
                "external dependency. Analytics scripts that are not essential "
                "for page function should be loaded asynchronously with async or defer.",
}

# Known third-party script domains and their categories.
KNOWN_THIRD_PARTY = {
    # Analytics
    "google-analytics.com":       "Google Analytics",
    "googletagmanager.com":       "Google Tag Manager",
    "analytics.google.com":       "Google Analytics",
    "static.hotjar.com":          "Hotjar",
    "script.hotjar.com":          "Hotjar",
    "cdn.segment.com":            "Segment",
    "cdn.amplitude.com":          "Amplitude",
    "mixpanel.com":               "Mixpanel",
    "js.hs-analytics.net":        "HubSpot Analytics",
    "js.hsforms.net":             "HubSpot Forms",
    # Advertising
    "googlesyndication.com":      "Google Ads",
    "doubleclick.net":            "Google DoubleClick",
    "facebook.net":               "Facebook Pixel",
    "connect.facebook.net":       "Facebook SDK",
    "platform.twitter.com":       "Twitter/X Widget",
    "ads.linkedin.com":           "LinkedIn Ads",
    "snap.licdn.com":             "LinkedIn Insight",
    # Social / embeds
    "platform.instagram.com":     "Instagram Embed",
    "cdn.embedly.com":            "Embedly",
    # Chat / support
    "js.intercomcdn.com":         "Intercom",
    "widget.intercom.io":         "Intercom",
    "static.zdassets.com":        "Zendesk",
    "js.driftt.com":              "Drift",
    # A/B testing
    "cdn.optimizely.com":         "Optimizely",
    "cdn-3.convertexperiments.com": "Convert",
    # Error tracking
    "browser.sentry-cdn.com":     "Sentry",
    "cdn.ravenjs.com":            "Sentry (legacy)",
}


def _extract_domain(src: str) -> str | None:
    """
    Extract the domain from a script src URL.

    Parameters:
        src (str): Script src attribute value.

    Returns:
        str | None: Domain string, or None if not an external URL.
    """
    src = src.strip().lower()
    if src.startswith("//"):
        src = "https:" + src
    if not (src.startswith("http://") or src.startswith("https://")):
        return None
    # Strip protocol and path.
    try:
        without_protocol = src.split("//", 1)[1]
        domain = without_protocol.split("/")[0]
        return domain
    except IndexError:
        return None


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Detect third-party scripts and flag them as informational supply-chain risks.

    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.

    Returns:
        list: One INFO finding per third-party script domain detected.
    """

    masLog(f"Running check: {METADATA['name']}")

    # Extract the page's own domain for comparison.
    page_domain = ""
    if url.startswith("http"):
        try:
            without_protocol = url.split("//", 1)[1]
            page_domain = without_protocol.split("/")[0].lower()
        except IndexError:
            pass

    findings = []
    reported_domains = set()

    for script in soup.find_all("script", src=True):
        src = script.get("src", "").strip()
        domain = _extract_domain(src)

        if not domain:
            continue

        # Skip same-domain scripts.
        if page_domain and domain == page_domain:
            continue

        # Skip already-reported domains — one finding per domain.
        if domain in reported_domains:
            continue

        reported_domains.add(domain)

        # Identify known third-party script.
        script_name = None
        for known_domain, name in KNOWN_THIRD_PARTY.items():
            if known_domain in domain:
                script_name = name
                break

        # Check for Subresource Integrity.
        has_sri = script.get("integrity", "").strip() != ""

        if script_name:
            display_name = f"{script_name} ({domain})"
        else:
            display_name = f"Unknown third-party script ({domain})"

        sri_note = "SRI integrity attribute present." if has_sri else "No SRI integrity attribute."

        masLog(
            f"{METADATA['name']} check: {display_name} detected",
            level="warning"
        )

        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": METADATA["severity"],
            "message":  f"Third-party script detected: {display_name}. "
                        f"External scripts represent a supply-chain risk — "
                        f"if the host is compromised, malicious code runs on your page. "
                        f"{sri_note}",
            "element":  str(script)[:120],
            "fix_hint": METADATA["fix_hint"],
            "line":   getattr(script, 'sourceline', None),
            "parent": "",
            "url":      url,
        })

    if not findings:
        masLog(f"{METADATA['name']} check: passed — no third-party scripts detected")

    return findings

