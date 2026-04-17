# checks/http_header_analyzer.py
# Check 47: HTTP security header analysis.
# Mosley Standard — Security/Operational (MS)
#
# HTTP response headers communicate security policies to browsers.
# Missing or misconfigured headers leave users vulnerable to:
#
#   - Content Security Policy (CSP): Missing CSP allows cross-site scripting
#     attacks that can inject malicious content into the page.
#
#   - X-Frame-Options / CSP frame-ancestors: Missing allows clickjacking —
#     the page can be embedded in an iframe on a malicious site.
#
#   - Strict-Transport-Security (HSTS): Missing means browsers may load
#     the page over HTTP even when HTTPS is available.
#
#   - X-Content-Type-Options: Missing allows MIME-type sniffing attacks.
#
#   - Referrer-Policy: Missing leaks the full URL to third parties.
#
#   - Permissions-Policy: Missing means the page cannot restrict access
#     to sensitive browser APIs (camera, microphone, geolocation).
#
# From an accessibility standpoint, security headers protect the integrity
# of accessible interfaces — injected scripts can override keyboard
# navigation, ARIA attributes, and focus management.
#
# This check requires a live HTTP request. It skips local file audits.

import urllib.request
import urllib.error
import config
from utils.logger import masLog
from bs4 import BeautifulSoup

METADATA = {
    "name":     "HTTP Header Analyzer",
    "wcag":     "MS",
    "level":    "MS",
    "severity": config.SEVERITY_MEDIUM,
    "fix_hint": "Configure security headers on your web server or CDN. "
                "Content-Security-Policy: restrict script/style sources. "
                "X-Frame-Options: DENY or SAMEORIGIN to prevent clickjacking. "
                "Strict-Transport-Security: max-age=31536000; includeSubDomains. "
                "X-Content-Type-Options: nosniff. "
                "Referrer-Policy: strict-origin-when-cross-origin. "
                "Use https://securityheaders.com to verify your configuration.",
}

# Headers to check and their descriptions.
SECURITY_HEADERS = {
    "content-security-policy": {
        "label":    "Content-Security-Policy (CSP)",
        "severity": config.SEVERITY_HIGH,
        "message":  "Missing Content-Security-Policy header. Without CSP, "
                    "cross-site scripting (XSS) attacks can inject malicious "
                    "scripts that override keyboard navigation and ARIA attributes.",
    },
    "x-frame-options": {
        "label":    "X-Frame-Options",
        "severity": config.SEVERITY_MEDIUM,
        "message":  "Missing X-Frame-Options header. The page can be embedded "
                    "in an iframe on a malicious site (clickjacking attack). "
                    "Recommended: X-Frame-Options: DENY or SAMEORIGIN.",
    },
    "strict-transport-security": {
        "label":    "Strict-Transport-Security (HSTS)",
        "severity": config.SEVERITY_MEDIUM,
        "message":  "Missing Strict-Transport-Security header. Browsers may "
                    "load the page over insecure HTTP even when HTTPS is available. "
                    "Recommended: Strict-Transport-Security: max-age=31536000.",
    },
    "x-content-type-options": {
        "label":    "X-Content-Type-Options",
        "severity": config.SEVERITY_LOW,
        "message":  "Missing X-Content-Type-Options header. Browsers may "
                    "MIME-sniff responses away from the declared content type. "
                    "Recommended: X-Content-Type-Options: nosniff.",
    },
    "referrer-policy": {
        "label":    "Referrer-Policy",
        "severity": config.SEVERITY_LOW,
        "message":  "Missing Referrer-Policy header. The full page URL may be "
                    "leaked to third-party services via the Referer header. "
                    "Recommended: Referrer-Policy: strict-origin-when-cross-origin.",
    },
    "permissions-policy": {
        "label":    "Permissions-Policy",
        "severity": config.SEVERITY_LOW,
        "message":  "Missing Permissions-Policy header. The page cannot restrict "
                    "access to sensitive browser APIs (camera, microphone, geolocation). "
                    "Recommended: Permissions-Policy: camera=(), microphone=(), geolocation=()",
    },
}


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Fetch HTTP response headers for the audited URL and flag missing
    security headers.

    Skips local file audits — headers are only available for live URLs.

    Parameters:
        soup (BeautifulSoup): Parsed HTML document (not used directly).
        url  (str):           The audited URL.

    Returns:
        list: One finding per missing security header.
    """

    masLog(f"Running check: {METADATA['name']}")

    # Skip local file audits.
    if not url.lower().startswith(("http://", "https://")):
        masLog(f"{METADATA['name']} check: skipped — not a live URL")
        return []

    # Fetch response headers.
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": config.REQUEST_HEADERS["User-Agent"]}
        )
        with urllib.request.urlopen(req, timeout=config.REQUEST_TIMEOUT) as response:
            headers = {k.lower(): v for k, v in response.headers.items()}
    except Exception as e:
        masLog(f"{METADATA['name']} check: could not fetch headers — {e}", level="warning")
        return []

    findings = []

    for header_key, header_info in SECURITY_HEADERS.items():
        if header_key in headers:
            masLog(f"{METADATA['name']} check: {header_info['label']} — present")
            continue

        # Special case: CSP frame-ancestors can substitute for X-Frame-Options.
        if header_key == "x-frame-options":
            csp = headers.get("content-security-policy", "")
            if "frame-ancestors" in csp.lower():
                masLog(f"{METADATA['name']} check: X-Frame-Options — covered by CSP frame-ancestors")
                continue

        masLog(
            f"{METADATA['name']} check: {header_info['label']} — missing",
            level="warning"
        )

        findings.append({
            "check":    METADATA["name"],
            "wcag":     METADATA["wcag"],
            "level":    METADATA["level"],
            "severity": header_info["severity"],
            "message":  header_info['message'],
            "element":  f"HTTP header: {header_key}",
            "fix_hint": METADATA["fix_hint"],
            "line":     None,
            "parent":   "",
            "url":      url,
        })

    if not findings:
        masLog(f"{METADATA['name']} check: passed — all security headers present")

    return findings