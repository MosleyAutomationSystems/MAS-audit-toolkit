# MAS Accessibility Audit Toolkit

A command-line and desktop accessibility auditing tool built to the Mosley Standard.
Accepts a URL or local HTML file and produces a structured, timestamped plain-text
report mapping findings to WCAG 2.1 AA success criteria.

Built by Damascus Mosley — Mosley Automation Systems (MAS)

---

## Who This Tool Is For

This toolkit is intended for:

- Developers performing quick accessibility diagnostics on web projects
- Small business website owners seeking accessibility risk indicators before a full audit
- Accessibility practitioners performing early-stage analysis and triage
- Students and researchers learning WCAG 2.1 AA criteria through applied tooling

This tool performs automated static analysis. It is not a replacement for manual
testing, screen reader evaluation, or certified accessibility auditing.

---

## What It Does

Runs ten automated accessibility checks against any webpage or local HTML file:

- **Alt Text** — flags `<img>` elements missing an `alt` attribute (WCAG 1.1.1)
- **H1 Count** — verifies exactly one `<h1>` exists per page (WCAG 1.3.1)
- **Heading Descent** — detects skipped heading levels, e.g. h1 → h4 (WCAG 2.4.6)
- **Form Labels** — finds `<input>` elements with no associated label (WCAG 1.3.1)
- **Language Attribute** — checks for a valid `lang` attribute on `<html>` (WCAG 3.1.1)
- **Tabindex Abuse** — flags positive `tabindex` values that disrupt focus order (WCAG 2.4.3)
- **Empty Links** — finds `<a>` elements with no accessible name (WCAG 2.4.4)
- **Empty Buttons** — finds `<button>` elements with no accessible name (WCAG 4.1.2)
- **Autoplay Media** — flags `<video>` and `<audio>` elements with autoplay (WCAG 1.4.2)
- **PDF Link Warnings** — finds PDF links whose text does not warn the user (WCAG 2.4.4)

Reports are deterministic and reproducible. Running the same audit on the same page
produces identical results unless the page changes.

Every run produces:
- A timestamped plain-text report saved to `/output`
- A timestamped log entry saved to `/logs`

---

## Sample Report Output

```
------------------------------------------------------------
MAS Accessibility Audit Toolkit v1.0.0
Source: https://example.com
Date: 2026-03-05 02:43:21
------------------------------------------------------------

[!] Alt Text — WCAG 1.1.1 (Level A)
     <img> missing alt attribute: src="hero-banner.jpg"

[!] Heading Structure — WCAG 2.4.6 (Level AA)
     Heading level skipped — jumped from h2 to h5: "Our Services"

[!] Empty Button — WCAG 4.1.2 (Level A)
     <button type="button"> has no accessible name. id="menu-toggle"

[OK] Language Attribute — WCAG 3.1.1 (Level A)
     lang attribute present and non-empty: "en"

[>] Report saved to: output/audit_20260305_024321_example.com.txt
------------------------------------------------------------
3 finding(s). Review complete.
```

---

## Requirements

- Python 3.13.1
- pip

---

## Installation

```
git clone https://github.com/MosleyAutomationSystems/MAS-audit-toolkit.git
cd MAS-audit-toolkit
pip install -r requirements.txt
```

---

## Usage

### Desktop GUI

```
py gui.py
```

Opens the MAS Accessibility Audit Toolkit desktop application. Enter a URL or
browse for a local HTML file, then click Run Audit or press Enter.

**GUI features:**
- Three-tab settings dialog with live preview
- Appearance — color theme (Dark, Light, High Contrast, CVD-Safe), font family, font size (14–20pt)
- Reading — dyslexia preset (Normal / Large / X-Large), word spacing, line height with reset
- Color Vision — CVD simulation (Normal, Protanopia, Deuteranopia, Tritanopia, Monochrome) and color adjustments (brightness, contrast, saturation, hue shift — each with reset)
- Settings persist across sessions via `gui_settings.json`

### Command Line

**Audit a live URL:**
```
py audit.py https://example.com
```

**Audit a local HTML file:**
```
py audit.py path\to\file.html
```

**View help:**
```
py audit.py --help
```

---

## Output

Reports are saved to the `/output` directory with timestamped filenames:
```
output/audit_20260305_010007_example.com.txt
```

Logs are saved to the `/logs` directory:
```
logs/audit_2026-03-05.log
```

---

## Project Structure

```
MAS-audit-toolkit/
├── audit.py              — CLI entry point
├── gui.py                — Desktop GUI (Tkinter)
├── reporter.py           — Report formatter and file writer
├── config.py             — All configurable values
├── requirements.txt      — Python dependencies
├── README.md             — This file
├── gui_settings.json     — Persisted GUI preferences (auto-generated on first run)
├── checks/
│   ├── __init__.py
│   ├── alt_text.py       — WCAG 1.1.1 alt attribute check
│   ├── headings.py       — WCAG 1.3.1 / 2.4.6 heading checks
│   ├── labels.py         — WCAG 1.3.1 form label check
│   ├── lang_attr.py      — WCAG 3.1.1 language attribute check
│   ├── tabindex.py       — WCAG 2.4.3 tabindex abuse check
│   ├── empty_links.py    — WCAG 2.4.4 empty link check
│   ├── empty_buttons.py  — WCAG 4.1.2 empty button check
│   ├── autoplay.py       — WCAG 1.4.2 autoplay media check
│   └── pdf_links.py      — WCAG 2.4.4 PDF link warning check
├── utils/
│   ├── __init__.py
│   ├── fetcher.py        — URL and file HTML loader
│   ├── validator.py      — Input validation and path traversal guard
│   └── logger.py         — masLog() timestamped logging
├── logs/                 — Runtime log files (not committed to Git)
└── output/               — Generated audit reports (not committed to Git)
```

---

## Mosley Standard Compliance

The Mosley Standard is an internal engineering framework developed by Mosley
Automation Systems to govern the quality, consistency, and accessibility of all
MAS-produced software. It is not a regulatory standard and does not constitute
third-party certification. Projects that pass the Mosley Standard checklist are
described as Mosley Standard compliant — not legally certified or externally audited.

| Pillar | Status |
|---|---|
| Infrastructure — dependency manifest, reproducible build, README | PASS |
| Operations — dry-run by default, error handling, logging, idempotent | PASS |
| Accessibility — keyboard navigation, focus indicators, contrast, screen reader support | PASS |
| Security — no eval(), input validation, path traversal guard, no secrets | PASS |

### Visual Disability Support (Mosley Standard Section 3.2)

| Requirement | Implementation |
|---|---|
| CVD-safe color usage | Amber replaces red; CVD-Safe theme uses Wong (2011) blue/orange palette |
| Non-color cues | `[!]` / `[OK]` / `[>]` prefixes on all result lines |
| Adjustable font size | 14–20pt with dyslexia presets (Normal / Large / X-Large) |
| Adjustable font family | 6 options, persisted across sessions |
| Three themes minimum | Four themes: Dark, Light, High Contrast, CVD-Safe |
| Dark / reduced brightness | Dark theme default; brightness slider available |
| Screen reader support | Announcement label with focus management (aria-live equivalent) |
| No keyboard traps | Tab / Shift-Tab exit results box cleanly (WCAG 2.1.2) |
| CVD simulation | Five modes via Vienot (1999) matrices |
| Color adjustments | Brightness, contrast, saturation, hue — each with reset |
| Word spacing | Normal / Wide / Wider presets |
| Line height | 1.0–3.0× slider with reset |

---

## Desktop Limitations

The following features are approximated in the Tkinter desktop app and will be
implemented with full precision in the web version:

| Feature | Desktop | Web version |
|---|---|---|
| Word spacing | Preset extra-space insertion (Normal / Wide / Wider) | Full CSS `word-spacing` in em units (0–2.5em) |
| Letter spacing | Not supported — excluded | Full CSS `letter-spacing` in em units (0–0.5em) |

---

## Roadmap

Planned features for future versions:

- **Multi-page site crawling** — follow internal links and audit an entire site in one run
- **Remediation guidance generation** — produce fix suggestions alongside each finding
- **Accessibility risk scoring** — assign a weighted score per page based on finding severity
- **Historical audit tracking** — compare results across runs to measure remediation progress

---

## Scope Note

This tool performs automated static analysis only. It covers a defined subset
of WCAG 2.1 AA criteria. Automated checks cannot replace manual testing,
screen reader evaluation, or human judgment. Findings are described as
risk indicators, not compliance verdicts.

This tool is not a certified accessibility audit and does not constitute
third-party compliance verification.
