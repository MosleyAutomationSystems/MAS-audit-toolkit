# config.py
# Central configuration for the MAS Accessibility Audit Toolkit.
# All configurable values live here. No magic numbers anywhere else in the project.
# If a value needs to change, it changes here and propagates everywhere automatically.

import os

# --- Directory Paths ---

# The root of the project, derived from this file's location.
# Using os.path.dirname(__file__) means these paths work correctly
# regardless of which directory you run the tool from.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Directory where timestamped .log files are written at runtime.
# os.path.join() builds the path correctly on Windows (\) and Unix (/) automatically.
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# Directory where generated plain-text audit reports are saved.
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

# --- Network Settings ---

# Maximum time in seconds to wait for a URL to respond before giving up.
# Without a timeout, a slow or unresponsive server hangs the tool indefinitely.
REQUEST_TIMEOUT = 10

# Headers we send with every HTTP request.
# Some servers block requests with no User-Agent, treating them as bots.
REQUEST_HEADERS = {
    'User-Agent': 'MAS-Accessibility-Audit-Toolkit/1.0'
    }
 # --- Parser Settings ---

# The HTML parsing engine BeautifulSoup will use.
# "lxml" is faster and more tolerant of malformed HTML than the built-in "html.parser".
# If lxml is not installed, this value is where you would change it — not in the check files.
HTML_PARSER = 'lxml'

# --- Report Settings ---

# Label that appears in report headers and log entries to identify the tool.
TOOL_NAME = "MAS Accessibility Audit Toolkit"

# Version string. Increment this manually when you make significant changes.
TOOL_VERSION = "1.0.0"

# The separator line used in plain-text reports to visually divide sections.
# Defined once here so every section break looks identical.
REPORT_SEPARATOR = "-" * 60

# --- Runtime Directories: Auto-Create on Import ---

# When config.py is imported anywhere in the project, logs/ and output/ are
# created automatically if they don't exist yet.
# exist_ok=True means no error is raised if the directory already exists — idempotent.
os.makedirs(LOGS_DIR, exist_ok=True)

os.makedirs(OUTPUT_DIR, exist_ok=True)
# --- Severity Taxonomy ---
# Single source of truth for all severity levels used across every check module.
# Checks reference these constants — never hardcode severity strings in check files.
SEVERITY_CRITICAL  = "critical"
SEVERITY_HIGH      = "high"
SEVERITY_MEDIUM    = "medium"
SEVERITY_LOW       = "low"
SEVERITY_INFO      = "info"

# --- Module Request Delay ---
# Seconds to wait between HTTP requests when running multiple checks.
# Prevents rate-limiting from target servers.
MODULE_REQUEST_DELAY = 1.5
