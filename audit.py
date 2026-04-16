# audit.py
# CLI entry point for the MAS Accessibility Audit Toolkit.
# Wires together: input validation, HTML loading, all ten checks, and reporting.

import argparse
import importlib
import pkgutil
from bs4 import BeautifulSoup

import checks
import config
from utils.logger import masLog
from utils.fetcher import load_html
from reporter import generate_report

def run_audit(source: str) -> None:
    """Run the full accessibility audit pipeline on a URL or local file."""

    masLog(f"Audit started — source: {source}")
    print(f"\n{config.TOOL_NAME} v{config.TOOL_VERSION}")
    print(f"Auditing: {source}")
    print(config.REPORT_SEPARATOR)

    # Step 1: Load HTML
    html = load_html(source)
    if html is None:
        print("ERROR: Could not load the source. Check the log for details.")
        masLog("Audit aborted — HTML could not be loaded", level="error")
        return

    # Step 2: Parse HTML
    soup = BeautifulSoup(html, config.HTML_PARSER)
    masLog("HTML parsed successfully")

     # Step 3: Discover and run all check modules automatically.
    # pkgutil.iter_modules walks the checks/ package directory.
    # Any module that exposes a run() function is treated as a check.
    # Adding a new check module to checks/ requires no changes here.
    all_findings = []
    for finder, module_name, _ in pkgutil.iter_modules(checks.__path__):
        module_config = config.MODULES.get(module_name, {})
        if not module_config.get("enabled", True):
            masLog(f"Skipping disabled module: checks.{module_name}")
            continue
        module = importlib.import_module(f"checks.{module_name}")
        if hasattr(module, "run"):
            masLog(f"Running module: checks.{module_name}")
            all_findings.extend(module.run(soup, source))

    # Step 4: Print summary to terminal
    print(f"Checks complete — {len(all_findings)} finding(s) found\n")

    if all_findings:
        for i, finding in enumerate(all_findings, start=1):
            severity = finding.get("severity", "low")
            prefix = "[!]" if severity in ("critical", "high", "medium") else "[>]"
            print(f"  {prefix} [{i}] {finding['check']} — WCAG {finding['wcag']} (Level {finding.get('level', 'MS')})")
            print(f"       {finding['message']}")
            print()

    # Step 5: Generate and save report
    report_path = generate_report(source, all_findings)
    print(config.REPORT_SEPARATOR)
    print(f"Report saved to: {report_path}")
    masLog(f"Audit complete — {len(all_findings)} finding(s)")


def main():
    parser = argparse.ArgumentParser(
        description=f"{config.TOOL_NAME} — WCAG 2.1 AA accessibility checker"
    )
    parser.add_argument(
        "source",
        metavar="URL_OR_FILE",
        help="URL (https://example.com) or local HTML file path to audit"
    )
    args = parser.parse_args()
    run_audit(args.source)


if __name__ == "__main__":
    main()