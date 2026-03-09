# reporter.py
# Generates a timestamped plain-text audit report grouped by severity.
# Mosley Standard compliant — findings sorted Critical > Moderate > Minor.
# Non-color cues ([!], [OK], [>]) used throughout — no color-only indicators.

import os
from datetime import datetime

import config
from utils.logger import masLog

# Severity display order — Critical first, Minor last.
SEVERITY_ORDER = ["critical", "moderate", "minor"]

# Human-readable labels and prefix cues for each severity level.
SEVERITY_META = {
    "critical": {
        "label":       "CRITICAL — Immediate Accessibility Barriers",
        "prefix":      "[!]",
        "description": "These issues prevent access for users with disabilities.",
    },
    "moderate": {
        "label":       "MODERATE — Usability Issues",
        "prefix":      "[!]",
        "description": "These issues significantly affect usability and should be addressed promptly.",
    },
    "minor": {
        "label":       "MINOR — Quality Improvements",
        "prefix":      "[>]",
        "description": "These issues are best-practice improvements.",
    },
}


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
        level = finding.get("severity", "minor")
        if level not in grouped:
            level = "minor"
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
        lines.append("[OK] No accessibility issues detected.")
        lines.append("")
    else:
        critical_count = len(grouped["critical"])
        moderate_count = len(grouped["moderate"])
        minor_count    = len(grouped["minor"])

        lines.append(f"[>] {total} finding(s) total:")
        lines.append(f"    [!] Critical : {critical_count}")
        lines.append(f"    [!] Moderate : {moderate_count}")
        lines.append(f"    [>] Minor    : {minor_count}")
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
    lines.append("    tabindex abuse, empty links, empty buttons,")
    lines.append("    autoplay media, PDF link warnings.")
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
