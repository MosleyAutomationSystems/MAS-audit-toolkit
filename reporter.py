# reporter.py
# Generates a timestamped plain-text audit report grouped by severity.
# Mosley Standard compliant — findings sorted Critical > Info, AAA in separate bucket.
# Non-color cues ([!], [OK], [>]) used throughout — no color-only indicators.
# WCAG_REPORT_LEVEL in config.py controls whether AAA findings are included.
# AAA findings are excluded from risk score calculation regardless of setting.

import os
from datetime import datetime

import config
from utils.logger import masLog

# Severity display order — Critical first, Minor last.
SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]

SEVERITY_META = {
    "critical": {
        "label":       "CRITICAL — Immediate Accessibility Barriers",
        "prefix":      "[!]",
        "description": "These issues block access entirely for users with disabilities.",
    },
    "high": {
        "label":       "HIGH — Significant Usability Issues",
        "prefix":      "[!]",
        "description": "These issues significantly affect usability and should be addressed promptly.",
    },
    "medium": {
        "label":       "MEDIUM — Moderate Usability Issues",
        "prefix":      "[!]",
        "description": "These issues affect some users and should be scheduled for remediation.",
    },
    "low": {
        "label":       "LOW — Quality Improvements",
        "prefix":      "[>]",
        "description": "These issues are best-practice improvements that reduce friction.",
    },
    "info": {
        "label":       "INFO — Informational",
        "prefix":      "[>]",
        "description": "These items are noted for awareness and do not require immediate action.",
    },
}

# Severity weights — sourced from config.py (single source of truth).
SEVERITY_WEIGHTS = config.SEVERITY_WEIGHTS

# Score bands — label and description.
RISK_BANDS = [
    (0,   0,   "PASS",     "No issues detected."),
    (1,   10,  "LOW",      "Minor issues only. Low risk to users."),
    (11,  25,  "MODERATE", "Usability issues present. Remediation recommended."),
    (26,  50,  "HIGH",     "Significant barriers present. Prompt remediation required."),
    (51,  999, "CRITICAL", "Severe access barriers. Immediate remediation required."),
]


def calculate_risk_score(findings: list) -> tuple[int, str, str]:
    """
    Calculate the Mosley Risk Score from a list of findings.

    Each finding is weighted by severity. The total score maps to a
    named risk band.

    Parameters:
        findings (list): List of finding dicts from check modules.

    Returns:
        tuple: (score: int, band: str, description: str)
    """
    score = sum(
        SEVERITY_WEIGHTS.get(f.get("severity", "low"), 0)
        for f in findings
    )

    for low, high, band, description in RISK_BANDS:
        if low <= score <= high:
            return score, band, description

    return score, "CRITICAL", RISK_BANDS[-1][3]

def _sanitize_source(source: str) -> str:
    """
    Convert a URL or file path into a safe filename fragment.
    Replaces characters that are invalid in Windows and Unix filenames.
    """
    safe = source.replace("https://", "").replace("http://", "")
    for char in r'\/: *?"<>|':
        safe = safe.replace(char, "_")
    return safe[:60]


def generate_report(source: str, findings: list) -> str:
    """
    Write a plain-text audit report grouped by severity to the output directory.

    Parameters:
        source   (str):  The audited URL or file path.
        findings (list): List of finding dictionaries from the check modules.

    Returns:
        str: Absolute path to the saved report file.
    """

    timestamp   = datetime.now()
    date_str    = timestamp.strftime("%Y%m%d_%H%M%S")
    safe_source = _sanitize_source(source)
    filename    = f"audit_{date_str}_{safe_source}.txt"
    report_path = os.path.join(config.OUTPUT_DIR, filename)

    masLog(f"Generating report: {filename}")

    # Separate AAA findings into their own bucket before any processing.
    # AAA findings never affect the risk score regardless of report level setting.
    # When WCAG_REPORT_LEVEL is "AA", AAA findings are excluded from output entirely.
    aaa_findings      = [f for f in findings if f.get("level") == "AAA"]
    scorable_findings = [f for f in findings if f.get("level") != "AAA"]

    include_aaa = (config.WCAG_REPORT_LEVEL == "AAA")

    # Group findings by severity level — AAA findings excluded from main grouping.
    grouped = {level: [] for level in SEVERITY_ORDER}
    for finding in scorable_findings:
        level = finding.get("severity", "low")
        if level not in grouped:
            level = "low"
        grouped[level].append(finding)

    lines = []

    # ── Header ──
    lines.append(config.REPORT_SEPARATOR)
    lines.append(f"{config.TOOL_NAME} v{config.TOOL_VERSION}")
    lines.append(f"Source : {source}")
    lines.append(f"Date   : {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(config.REPORT_SEPARATOR)
    lines.append("")

    # ── Summary ──
    # Total for display uses all findings.
    # Risk score and grouping use scorable_findings (AAA excluded).
    total = len(scorable_findings)
    total_with_aaa = len(findings)
    if total == 0:
        lines.append("[OK] PASS — No accessibility issues detected.")
        lines.append("  [>] Mosley Risk Score : 0 — PASS")
        lines.append("")
        lines.append("     All checks passed. No findings to report.")
        lines.append("")
    else:
        critical_count = len(grouped["critical"])
        high_count     = len(grouped["high"])
        medium_count   = len(grouped["medium"])
        low_count      = len(grouped["low"])
        info_count     = len(grouped["info"])

        # WCAG level breakdown
        level_a_count  = sum(1 for f in findings if f.get("level") == "A")
        level_aa_count = sum(1 for f in findings if f.get("level") == "AA")
        level_aaa_count = sum(1 for f in findings if f.get("level") == "AAA")

        # Blocking count — critical + high require immediate action
        # Risk score calculated from scorable_findings only - AAA excluded.
        blocking = critical_count + high_count

        status = "[!] FAIL" if blocking > 0 else "[>] REVIEW"

        score, band, band_desc = calculate_risk_score(scorable_findings)

        lines.append(f"{status} — {total} finding(s) detected")
        lines.append(f"  [>] Mosley Risk Score : {score} — {band}")
        lines.append(f"       {band_desc}")
        lines.append("")
        lines.append("  By severity:")
        lines.append(f"    [!] Critical : {critical_count}")
        lines.append(f"    [!] High     : {high_count}")
        lines.append(f"    [!] Medium   : {medium_count}")
        lines.append(f"    [>] Low      : {low_count}")
        lines.append(f"    [>] Info     : {info_count}")
        lines.append("")
        lines.append("  By WCAG level:")
        lines.append(f"    [>] Level A   : {level_a_count}")
        lines.append(f"    [>] Level AA  : {level_aa_count}")
        lines.append(f"    [>] Level AAA : {level_aaa_count}")
        lines.append("")
        if blocking > 0:
            lines.append(f"  [!] {blocking} blocking issue(s) require immediate attention.")
        else:
            lines.append("  [>] No blocking issues. Review low/info findings.")
        if include_aaa and aaa_findings:
            lines.append(f"  [>] {len(aaa_findings)} AAA finding(s) listed separately below.")
        lines.append("")
        lines.append(config.REPORT_SEPARATOR)
        lines.append("")

        # ── Findings grouped by severity ──
        finding_number = 1
        for level in SEVERITY_ORDER:
            level_findings = grouped[level]
            if not level_findings:
                continue

            meta = SEVERITY_META[level]
            lines.append(f"{meta['prefix']} {meta['label']}")
            lines.append(f"    {meta['description']}")
            lines.append("")

            for finding in level_findings:
                lines.append(
                    f"  [{finding_number}] {finding['check']} "
                    f"— WCAG {finding['wcag']} (Level {finding.get('level', 'MS')})"
                )
                # Line number and parent context.
                line_no = finding.get("line")
                parent  = finding.get("parent", "").strip()
                if line_no:
                    lines.append(f"       Line {line_no}" + (f" — {parent}" if parent else ""))
                lines.append(f"       {finding['message']}")
                # Suggested remediation.
                fix_hint = finding.get("fix_hint", "")
                if fix_hint:
                    lines.append(f"       Remediation: {fix_hint}")
                lines.append("")
                finding_number += 1

            lines.append(config.REPORT_SEPARATOR)
            lines.append("")
    # ── Accessibility Fix Guide ──
    if findings:
        lines.append("[>] ACCESSIBILITY FIX GUIDE")
        lines.append("    One recommended fix per issue type detected.")
        lines.append("")

        seen_checks = set()
        for finding in findings:
            check_name = finding.get("check", "")
            fix_hint   = finding.get("fix_hint", "")
            if check_name in seen_checks or not fix_hint:
                continue
            seen_checks.add(check_name)
            lines.append(f"  [>] {check_name}")
            lines.append(f"       {fix_hint}")
            lines.append("")

        lines.append(config.REPORT_SEPARATOR)
        lines.append("")
    # ── AAA Bucket (C16) ──
    # Only rendered when WCAG_REPORT_LEVEL is "AAA".
    # Collapsed by default — clearly labeled as not legally required.
    if include_aaa and aaa_findings:
        lines.append("[>] AAA — ENHANCED ACCESSIBILITY (NOT LEGALLY REQUIRED)")
        lines.append("    The following findings are WCAG 2.1 AAA level.")
        lines.append("    AAA conformance is not required by ADA, Section 508,")
        lines.append("    or most accessibility laws. These are documented for")
        lines.append("    reference only and do not affect your risk score.")
        lines.append("")

        seen_aaa = set()
        for finding in aaa_findings:
            lines.append(
                f"  [>] {finding['check']} "
                f"— WCAG {finding['wcag']} (Level AAA)"
            )
            lines.append(f"       {finding['message']}")
            lines.append("")

        lines.append("  Fix hints for AAA findings:")
        for finding in aaa_findings:
            check_name = finding.get("check", "")
            fix_hint   = finding.get("fix_hint", "")
            if check_name not in seen_aaa and fix_hint:
                lines.append(f"    [>] {check_name}: {fix_hint}")
                seen_aaa.add(check_name)

        lines.append(config.REPORT_SEPARATOR)
        lines.append("")

    # ── Footer ──
    lines.append("[>] Checks performed:")
    lines.append("    alt text, heading structure, form labels, lang attribute,")
    lines.append("    tabindex abuse, empty links, empty buttons, autoplay media,")
    lines.append("    PDF link warnings, page title, duplicate IDs,")
    lines.append("    landmark roles, skip navigation link, accessibility patterns,")
    lines.append("    platform detection, viewport meta, touch target CSS check, table scope attributes,")
    lines.append("    figure/figcaption check, animated GIF detection, iframe title check, svg accessibility check,")
    lines.append("    outline:none detection, fieldset/legend check, autocomplete attribute check, multiple nav label check,")
    lines.append("    skip link target validation, main uniqueness check, lang on language switches, small text detection,")
    lines.append("    justified text detection, all-caps text detection, mailto link warning, document link warning,")
    lines.append("    aria-hidden on focusable elements,aria-required consistency, aria-describedby orphan check, aria-role validity check,")
    lines.append("    image map check, rtl direction check, meta description check,")
    lines.append("    robots meta tag check, mixed content check, third-party script detection, ")
    lines.append("")
    lines.append(
        "Note: This report covers a defined subset of WCAG 2.1 AA criteria. "
        "Findings are risk indicators, not compliance verdicts."
    )
    lines.append(config.REPORT_SEPARATOR)

    # ── Write to file ──
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    masLog(f"Report saved: {report_path}")
    return report_path
