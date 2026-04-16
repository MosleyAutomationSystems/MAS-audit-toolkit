# utils/logger.py
# Provides masLog() — the single logging function used by every part of the toolkit.
# All timestamped log entries flow through here. Nothing else in the project
# writes to logs directly.

import logging
import os
from datetime import datetime

# Import our central config so we know where to write log files.
import config

# --- Build the log file path ---

# Generate a filename using today's date (e.g. "audit_2025-03-04.log").
# This means each day gets its own log file automatically.
# strftime() formats a datetime object into a string using format codes.
# %Y = four-digit year, %m = two-digit month, %d = two-digit day.
_log_filename = datetime.now().strftime("audit_%Y-%m-%d.log")

# Join the logs directory path from config with the filename.
# Result: D:\Dev\MAS-audit-toolkit\logs\audit_2025-03-04.log
_log_filepath = os.path.join(config.LOGS_DIR, _log_filename)

# --- Configure the logger ---

# logging.basicConfig() sets up the root logger with our chosen settings.
# This only needs to run once — subsequent imports of this module reuse it.
os.makedirs(config.LOGS_DIR, exist_ok=True)  # Ensure logs/ directory exists before configuring logging
logging.basicConfig(
    # Write log entries to our timestamped file.
    filename=_log_filepath,

    # If the log file already exists, append to it rather than overwrite.
    # This is what makes logging idempotent — running the tool twice on the
    # same day adds to the same file rather than destroying prior entries.
    filemode="a",

    # The format of each log entry.
    # %(asctime)s = timestamp, %(levelname)s = INFO/WARNING/ERROR,
    # %(message)s = the text we pass to masLog().
    format="%(asctime)s | %(levelname)s | %(message)s",

    # Timestamp format: 2025-03-04 14:32:01
    datefmt="%Y-%m-%d %H:%M:%S",

    # Only record entries at INFO level and above (INFO, WARNING, ERROR).
    # DEBUG messages are silently ignored unless we change this value in config.
    level=logging.INFO,
)

# Get the named logger instance for this toolkit.
# Using a named logger (instead of the root logger) means our entries
# are clearly identified if this tool is ever embedded in a larger system.
_logger = logging.getLogger("mas_audit")

# --- Public function ---

def masLog(message: str, level: str = "info") -> None:
    """
    Write a timestamped log entry to the daily audit log file.

    Parameters:
        message (str): The text to log.
        level (str): Severity level — "info", "warning", or "error".
                     Defaults to "info" if not specified.

    Usage:
        masLog("Audit started for https://example.com")
        masLog("Missing alt text on 3 images", level="warning")
        masLog("Failed to fetch URL", level="error")
    """

    # Normalize the level string to lowercase so "INFO", "Info", and "info"
    # all work the same way. Defensive programming against caller typos.
    level = level.lower()

    # Route the message to the correct logging method based on level.
    if level == "warning":
        _logger.warning(message)
    elif level == "error":
        _logger.error(message)
    else:
        # Default to info for anything unrecognized, not a crash.
        _logger.info(message)
#```

#---

#**Test it now.** Run this in your terminal:
#```
#python -c "from utils.logger import masLog; masLog('Logger test successful')"
#```

#No output in the terminal is correct — log entries go to the file, not the screen. So then run:
#```
#type logs\audit_2025-03-04.log
#```

#Replace the date with today's date. You should see one line like:
#```
#2025-03-04 14:32:01 | INFO | Logger test successful