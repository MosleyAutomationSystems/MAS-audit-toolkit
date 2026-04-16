# checks/platform_detection.py
# Check 15: Platform-locked CMS detection.
# Mosley Standard — Platform Restriction (MS)
# Identifies sites hosted on third-party CMS platforms where the owner
# cannot directly modify HTML, ARIA, or CSS to implement remediation.
# When a platform is detected, all findings on the site carry an implicit
# restriction: the fixes are documented, but the client cannot implement
# them without migrating to an owner-controlled platform.
# This is an informational finding — not a WCAG violation.

from bs4 import BeautifulSoup
import config
from utils.logger import masLog

METADATA = {
    "name": "Platform Detection",
    "wcag": "MS",
    "level": "MS",
    "severity": config.SEVERITY_INFO,
    "fix_hint": "This site is hosted on a platform-locked CMS. Direct HTML, "
                "ARIA, and CSS remediation is not possible without access to "
                "the underlying template or source files. The complete "
                "remediation path is to migrate the site to an owner-controlled "
                "platform (e.g. GitHub Pages, custom host) where all findings "
                "in this report can be implemented directly.",
}

# Each entry: (platform_name, detection_rules)
# Detection rules are checked in order: meta generator, script src patterns,
# link href patterns, body class patterns.
# First match wins — one finding per page, not one per signal.

PLATFORMS = [
    (
        "Squarespace",
        {
            "meta_generator": ["Squarespace"],
            "script_src": ["static.squarespace.com", "squarespace.com"],
            "link_href": [],
            "body_class": []
        }
    ),
    (
        "Wix",
        {
            "meta_generator": ["Wix.com", "wix"],
            "script_src": ["static.parastorage.com", "wix.com"],
            "link_href": [],
            "body_class": []
        }
    ),
    (
        "Weebly",
        {
            "meta_generator": ["Weebly"],
            "script_src": ["editmysite.com", "weebly.com"],
            "link_href": [],
            "body_class": [],
        }
    ),
    (
        "Shopify",
        {
            "meta_generator": ["Shopify"],
            "script_src": ["shopify.com"],
            "link_href": [],
            "body_class": [],
        }
    ),
    (
        "Google Sites",
        {
            "meta_generator": ["Google Sites", "jotspot"],
            "script_src": ["sites.google.com"],
            "link_href": ["sites.google.com"],
            "body_class": [],
        }
    ),
    (
        "Webflow",
        {
            "meta_generator": ["Webflow"],
            "script_src": ["webflow.com", "assets.website-files.com"],
            "link_href": [],
            "body_class": ["w-mod-"],  # Webflow adds classes like w-mod-js, w-mod-touch to <body>
        }
    ),
    (
        "res-menu.net",
        {
            "meta_generator": [],
            "script_src": ["res-menu.net"],
            "link_href": ["res-menu.net"],
            "body_class": [],
        }
    ),
    (
        "WordPress.com (hosted)",
        {
            "meta_generator": [],
            "script_src": ["s0.wp.com", "s1.wp.com", "s2.wp.com"],
            "link_href": [],
            "body_class": [],
        }
    ),
    (
        "GoDaddy Website Builder",
        {
            "meta_generator": ["GoDaddy Website Builder"],
            "script_src": ["secureserver.net"],
            "link_href": [],
            "body_class": [],
        }
    ),
    (
        "Jimdo",
        {
            "meta_generator": ["Jimdo"],
            "script_src": ["jimcdn.com", "jimdostatic.com"],
            "link_href": ["jimdostatic.com"],
            "body_class": [],
        }
    ),
    (
        "strikingly",
        {
            "meta_generator": ["strikingly"],
            "script_src": ["strikingly.com", "strikinglycdn.com"],
            "link_href": ["strikinglycdn.com"],
            "body_class": [],
        }
    ),
    (
        "site123",
        {
            "meta_generator": ["site123"],
            "script_src": ["site123.com", "editorassets.com"],
            "link_href": [],
            "body_class": [],
        }
    ),
    (
        "Duda",
        {
            "meta_generator": ["Duda"],
            "script_src": ["irp.cdn-website.com", "lirp.cdn-website.com", "du-cdn.com"],
            "link_href": [],
            "body_class": ["dmBody"],
        }
    ),
    (
        "Framer",
        {
            "meta_generator": ["Framer"],
            "script_src": ["framer.com", "framerusercontent.com"],
            "link_href": ["framerusercontent.com"],
            "body_class": [],
        }
    ),
    (
        "Tilda",
        {
            "meta_generator": ["Tilda"],
            "script_src": ["tildacdn.com", "tilda.ws"],
            "link_href": ["tildacdn.com"],
            "body_class": [],
        }
    ),
    (
        "BentoBox",
        {
            "meta_generator": ["BentoBox"],
            "script_src": ["bento.com", "bentobox.com"],
            "link_href": ["getbento.com"],
            "body_class": [],
        }
    ),
    (
        "Popmenu",
        {
            "meta_generator": ["Popmenu"],
            "script_src": ["popmenu.com", "assets.popmenu.com"],
            "link_href": [],
            "body_class": [],
        }
    ),
    (
        "SinglePlatform",
        {
            "meta_generator": ["SinglePlatform"],
            "script_src": ["singleplatform.com"],
            "link_href": ["singleplatform.com"],
            "body_class": [],
        }
    ),
    (
        "Toast",
        {
            "meta_generator": ["toasttab"],
            "script_src": ["toasttab.com", "cdn.toasttab.com"],
            "link_href": ["toasttab.com"],
            "body_class": [],
        }
    ),
]


def _detect_platform(soup: BeautifulSoup):
    """
    Scan the parsed document for platform fingerprints.
 
    Checks in this order:
      1. <meta name="generator"> content
      2. <script src="..."> attributes
      3. <link href="..."> attributes
      4. <body class="..."> tokens
 
    Returns the platform name string on first match, or None if no
    known platform is detected.
 
    Parameters:
        soup (BeautifulSoup): Parsed HTML document.
 
    Returns:
        str | None: Platform name, or None.
    """

    # 1. Meta generator tag
    generator_tag = soup.find("meta", attrs={"name": "generator"})
    generator_val = (generator_tag.get("content", "") if generator_tag else "").lower()     

    # 2. All script src values 
    script_srcs = [
        (tag.get("src", "") or "").lower() 
        for tag in soup.find_all("script", src=True)
    ]

    # 3. All link href values
    link_hrefs = [
        (tag.get("href", "") or "").lower() 
        for tag in soup.find_all("link", href=True)
    ]

    # 4. All body class tokens
    body_tag = soup.find("body")
    body_classes = " ".join(body_tag.get("class", []) if body_tag else []).lower()

    for platform_name, rules in PLATFORMS:
        # Check meta generator
        if any(sig in generator_val for sig in rules["meta_generator"]):
            return platform_name

        # Check script src values
        if any(
            sig in src
            for sig in rules["script_src"]
            for src in script_srcs
        ):
            return platform_name

        # Check link href values
        if any(
            sig in href 
            for sig in rules["link_href"]
            for href in link_hrefs  
        ):
            return platform_name

        # Check body class tokens
        if any(sig in body_classes for sig in rules["body_class"]):
            return platform_name

    return None


def run(soup: BeautifulSoup, url: str = "") -> list:
    """
    Detect whether the page is hosted on a platform-locked CMS.
 
    If a known platform is detected, returns one INFO-level finding
    flagging the site as PLATFORM RESTRICTED. If no known platform
    is detected, returns an empty list — no finding is raised.
 
    Parameters:
        soup (BeautifulSoup): A parsed HTML document.
        url  (str):           Optional URL of the document being checked.
 
    Returns:
        list: One INFO finding if a platform is detected, or empty list.
    """

    masLog(f"Running check: {METADATA['name']}")

    platform = _detect_platform(soup)

    if platform is None:
        masLog(f"{METADATA['name']} check: passed -  No platform lock detected.")
        return []
    
    masLog(
        f"{METADATA['name']} check: platform detected - {platform}. ",
        level="warning "
    )

    return [{
        "check": METADATA["name"],
        "wcag": METADATA["wcag"],
        "severity": METADATA["severity"],
        "message": f"[PLATFORM RESTRICTED] Site is hosted on {platform}. "
                    "Direct HTML, ARIA, and CSS remediation is not available "
                    "without access to the underlying template or source files. "
                    "All findings in this report are documented for reference "
                    "but cannot be implemented on this platform without "
                    "migrating to an owner-controlled host.",
        "element":  f"Platform: {platform}",
        "fix_hint": METADATA["fix_hint"],
        "line":   None,
        "parent": "",
        "url":      url,
    }]


