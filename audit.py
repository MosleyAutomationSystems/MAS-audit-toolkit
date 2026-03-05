# audit.py
# CLI entry point for the MAS Accessibility Audit Toolkit.
# Wires together: input validation, HTML loading, all ten checks, and reporting.

import argparse
from bs4 import BeautifulSoup

import config
from utils.logger import masLog
from utils.fetcher import load_html
from checks.alt_text import check_alt_text
from checks.headings import check_headings
from checks.labels import check_labels
from checks.lang_attr import check_lang_attr
from checks.tabindex import check_tabindex
from checks.empty_links import check_empty_links
from checks.empty_buttons import check_empty_buttons
from checks.autoplay import check_autoplay
from checks.pdf_links import check_pdf_links
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

    # Step 3: Run all ten checks
    all_findings = []
    all_findings.extend(check_alt_text(soup))
    all_findings.extend(check_headings(soup))
    all_findings.extend(check_labels(soup))
    all_findings.extend(check_lang_attr(soup))
    all_findings.extend(check_tabindex(soup))
    all_findings.extend(check_empty_links(soup))
    all_findings.extend(check_empty_buttons(soup))
    all_findings.extend(check_autoplay(soup))
    all_findings.extend(check_pdf_links(soup))

    # Step 4: Print summary to terminal
    print(f"Checks complete — {len(all_findings)} finding(s) found\n")

    if all_findings:
        for i, finding in enumerate(all_findings, start=1):
            print(f"  [{i}] {finding['check']} — WCAG {finding['wcag']}")
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