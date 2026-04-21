# MAS Accessibility Audit Toolkit

A command-line and desktop accessibility auditing tool built to the Mosley Standard.  
Accepts a URL or local HTML file and produces a structured, timestamped plain-text  
report mapping findings to WCAG 2.1 AA success criteria, with severity grouping,  
line numbers, parent context, and suggested remediation for every finding.

Built by Damascus Mosley — Mosley Automation Systems (MAS)  
CIS Student · Michigan Reconnect Scholar · Grand Rapids Community College

---

## What It Does

Runs 15 automated accessibility checks against any webpage or local HTML file.  
Findings are grouped by severity (Critical → Info), mapped to WCAG 2.1 AA criteria,  
and each finding includes a suggested remediation step.

Automated tools cover approximately 30–40% of WCAG 2.1 AA failures.  
This toolkit does not replace manual testing, screen reader evaluation, or human judgment.  
All findings are risk indicators — not compliance verdicts.

---

## Check Modules (15 Built)

### WCAG Checks — Level A

| # | Module | WCAG | Severity |
|---|--------|------|----------|
| 1 | Alt Text Detection | 1.1.1 | Critical |
| 2 | Heading Structure | 1.3.1 / 2.4.6 | High |
| 3 | Form Labels | 1.3.1 | High |
| 4 | Language Attribute | 3.1.1 | High |
| 5 | Tabindex Abuse | 2.4.3 | Critical |
| 6 | Empty Links | 2.4.4 | High |
| 7 | Empty Buttons | 4.1.2 | High |
| 8 | Autoplay Media | 1.4.2 | High |
| 9 | PDF Link Warning | 2.4.4 | Low |
| 10 | Page Title | 2.4.2 | Critical |
| 11 | Duplicate IDs | 4.1.1 | Critical |
| 12 | Landmark Roles | 2.4.1 | High |
| 13 | Skip Navigation Link | 2.4.1 | High |
| 14 | Accessibility Patterns | 2.4.4 | Varies |

### Platform Detection

| # | Module | Notes |
|---|--------|-------|
| 15 | Platform Detection | Identifies 19 CMS platforms across 4 signal vectors. Flags platform-locked sites as PLATFORM RESTRICTED. |

---

## Report Format

Every finding includes:

- Severity level and WCAG criterion
- Source line number (where available)
- Finding message with element identifier
- Suggested remediation step

```
[!] CRITICAL — Immediate Accessibility Barriers

  [1] aria-hidden on Focusable Elements — WCAG 4.1.2 (Level A)
       Line 42
       <button> has aria-hidden="true" but is still keyboard focusable.
       Remediation: Never place aria-hidden="true" on an element that can
       receive keyboard focus. Use display:none or tabindex="-1" instead.
```

The Mosley Risk Score summarizes the audit in a single number mapped to a named band:

| Score | Band | Meaning |
|-------|------|---------|
| 0 | PASS | No issues detected |
| 1–10 | LOW | Minor issues only |
| 11–25 | MODERATE | Remediation recommended |
| 26–50 | HIGH | Prompt remediation required |
| 51+ | CRITICAL | Immediate remediation required |

---

## Requirements

- Python 3.13+
- pip

---

## Installation

```bash
git clone https://github.com/MosleyAutomationSystems/MAS-audit-toolkit.git
cd MAS-audit-toolkit
pip install -r requirements.txt
```

---

## Usage

### Desktop GUI

```bash
python gui.py
```

Opens the MAS Accessibility Audit Toolkit desktop application. Enter a URL or  
browse for a local HTML file, then click Run Audit or press Enter.

**GUI features:**

- Three-tab settings dialog with live preview
- Appearance — color theme (Dark, Light, High Contrast, CVD-Safe), font family, font size (14–20pt)
- Reading — dyslexia preset (Normal / Large / X-Large), word spacing, line height with reset
- Color Vision — CVD simulation (Normal, Protanopia, Deuteranopia, Tritanopia, Monochrome)
- Large Targets toggle — scales all interactive elements to 48px minimum (Mosley Standard Category 5)
- Settings persist across sessions via `gui_settings.json`

### Command Line

**Audit a live URL:**

```bash
python audit.py https://example.com
```

**Audit a local HTML file:**

```bash
python audit.py path/to/file.html
```

**View help:**

```bash
python audit.py --help
```

**CLI features:**

- Runs all 15 check modules against any URL or local HTML file
- Findings grouped by severity (Critical → High → Medium → Low → Info)
- Each finding includes WCAG criterion, line number, element context, and remediation step
- Mosley Risk Score printed at summary
- Report saved automatically to `/output` with timestamped filename
- All activity logged to `/logs`
- Platform Detection flags CMS-locked sites as PLATFORM RESTRICTED
- AAA findings suppressed by default — enable via `WCAG_REPORT_LEVEL = "AAA"` in `config.py`

---

## Output

Reports are saved to the `/output` directory with timestamped filenames:

```
output/audit_20260416_141057_shopify.com.txt
```

Logs are saved to the `/logs` directory:

```
logs/audit_2026-04-16.log
```

---

## Project Structure

```
MAS-audit-toolkit/
├── audit.py              — CLI entry point
├── gui.py                — Desktop GUI (Tkinter)
├── reporter.py           — Report formatter and file writer
├── config.py             — All configurable values (single source of truth)
├── requirements.txt      — Python dependencies
├── README.md             — This file
├── gui_settings.json     — Persisted GUI preferences (auto-generated on first run)
├── checks/               — 15 check modules (auto-discovered)
│   ├── __init__.py
│   ├── alt_text.py
│   ├── autoplay.py
│   ├── duplicate_ids.py
│   ├── empty_buttons.py
│   ├── empty_links.py
│   ├── headings.py
│   ├── labels.py
│   ├── landmark_roles.py
│   ├── lang_attr.py
│   ├── patterns.py
│   ├── pdf_links.py
│   ├── platform_detection.py
│   ├── skip_link.py
│   ├── tabindex.py
│   └── title_element.py
├── utils/
│   ├── __init__.py
│   ├── fetcher.py        — URL and file HTML loader
│   ├── validator.py      — Input validation and path traversal guard
│   └── logger.py         — masLog() timestamped logging
├── logs/                 — Runtime log files (not committed to Git)
└── output/               — Generated audit reports (not committed to Git)
```

---

## WCAG Report Level

By default the toolkit runs in AA mode. AAA findings are detected but suppressed  
from the main report and excluded from the risk score.

To include AAA findings, set in `config.py`:

```python
WCAG_REPORT_LEVEL = "AAA"
```

---

## Paid License

The free open-source tier includes 15 built modules. A paid desktop license  
adds all future modules as they ship, extended customization features, branded  
PDF/DOCX report export, and batch scanning via CLI.

Individual license — $129 one-time · 1 seat  
Small Agency license — $259 one-time · 1–5 seats

Contact: mosleyautomationsystems@gmail.com

---

## Mosley Standard Compliance

| Pillar | Status |
|--------|--------|
| Infrastructure — dependency manifest, reproducible build, README | PASS |
| Operations — error handling, logging, idempotent, dry-run | PASS |
| Accessibility — keyboard navigation, focus indicators, contrast, screen reader support | PASS |
| Security — no eval(), input validation, path traversal guard, no secrets | PASS |

### Visual Disability Support (Mosley Standard Section 3.2)

| Requirement | Implementation |
|-------------|---------------|
| CVD-safe color usage | Amber replaces red; CVD-Safe theme uses Wong (2011) palette |
| Non-color cues | `[!]` / `[OK]` / `[>]` prefixes on all result lines |
| Adjustable font size | 14–20pt with dyslexia presets |
| Adjustable font family | 6 options, persisted across sessions |
| Four themes | Dark, Light, High Contrast, CVD-Safe |
| Dark / reduced brightness | Dark theme default; brightness slider available |
| Screen reader support | Announcement label with focus management |
| No keyboard traps | Tab / Shift-Tab exit results box cleanly (WCAG 2.1.2) |
| CVD simulation | Five modes via Vienot (1999) matrices |
| Color adjustments | Brightness, contrast, saturation, hue — each with reset |
| Word spacing | Normal / Wide / Wider presets |
| Line height | 1.0–3.0× slider with reset |
| Large Targets toggle | Scales GUI interactive elements to 48px (Mosley Standard Category 5) |

---

## Known Issues

Git Bash on Windows may display `▒` characters in CLI output instead of separator lines.  
This is a terminal encoding artifact only — CMD and the desktop GUI render correctly.

---

## Scope Note

This tool performs automated static analysis only. It covers a defined subset  
of WCAG 2.1 AA criteria. Automated checks cannot replace manual testing,  
screen reader evaluation, or human judgment. Findings are described as  
risk indicators, not compliance verdicts.

This tool is not a certified accessibility audit and does not constitute  
third-party compliance verification.

MAS is not a licensed accessibility consultant or certified auditor.  
Damascus Mosley is a CIS student at Grand Rapids Community College  
building real-world, portfolio-driven projects.
