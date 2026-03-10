# reporter.py
# Generates a timestamped plain-text audit report grouped by severity.
# Mosley Standard compliant — findings sorted Critical > Moderate > Minor.
# Non-color cues ([!], [OK], [>]) used throughout — no color-only indicators.

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

# Severity weights for risk score calculation.
SEVERITY_WEIGHTS = {
    "critical": 10,
    "high":      5,
    "medium":    2,
    "low":       1,
    "info":      0,
}
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

    # Group findings by severity level.
    grouped = {level: [] for level in SEVERITY_ORDER}
    for finding in findings:
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
    total = len(findings)
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
        blocking = critical_count + high_count

        status = "[!] FAIL" if blocking > 0 else "[>] REVIEW"

        score, band, band_desc = calculate_risk_score(findings)

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
                    f"— WCAG {finding['wcag']} (Level {finding['level']})"
                )
                lines.append(f"       {finding['message']}")
                lines.append("")
                finding_number += 1

            lines.append(config.REPORT_SEPARATOR)
            lines.append("")

    # ── Footer ──
    lines.append("[>] Checks performed:")
    lines.append("    alt text, heading structure, form labels, lang attribute,")
    lines.append("    tabindex abuse, empty links, empty buttons, autoplay media,")
    lines.append("    PDF link warnings, page title, duplicate IDs,")
    lines.append("    landmark roles, skip navigation link.")
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
