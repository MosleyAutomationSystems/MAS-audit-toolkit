# utils/validator.py
# Input validation for the MAS Accessibility Audit Toolkit.
# All user-supplied inputs (URLs and file paths) are checked here
# before anything else in the program touches them.
# This is the security gate — nothing bypasses this module.

import os
import re

from utils.logger import masLog

# --- URL Validation ---

# A minimal regex pattern that matches http:// or https:// URLs only.
# We do not accept ftp://, file://, or bare domain names.
# ^ = start of string, $ = end of string, re.IGNORECASE = case insensitive.
_URL_PATTERN = re.compile(
    r'^https?://'        # Must start with http:// or https://
    r'[a-zA-Z0-9\-.]+'  # Domain name: letters, numbers, hyphens, dots
    r'(\.[a-zA-Z]{2,})' # Top-level domain: at least 2 letters (e.g. .com, .org)
    r'.*$',             # Anything after (path, query string, etc.)
    re.IGNORECASE
)

def validate_url(url: str) -> bool:
    """
    Check that a URL is a valid http:// or https:// address.

    Parameters:
        url (str): The URL string supplied by the user.

    Returns:
        bool: True if the URL passes validation, False if it does not.
    """

    # Strip leading/trailing whitespace the user may have accidentally included.
    url = url.strip()

    # Test the URL against our pattern.
    # re.match() only checks from the start of the string, which is what we want.
    if not _URL_PATTERN.match(url):
        # Log the rejection so there is an audit trail of bad inputs.
        masLog(f"URL validation failed: '{url}' does not match required pattern", level="warning")
        return False

    masLog(f"URL validation passed: '{url}'")
    return True


# --- File Path Validation ---

def validate_filepath(filepath: str) -> bool:
    """
    Check that a local file path is safe and points to a real HTML file.

    Specifically guards against:
    - Path traversal attacks (../ sequences trying to escape the project directory)
    - Paths that point to non-existent files
    - Files that are not .html or .htm

    Parameters:
        filepath (str): The file path string supplied by the user.

    Returns:
        bool: True if the path passes all checks, False if any check fails.
    """

    # Strip whitespace.
    filepath = filepath.strip()

    # os.path.abspath() resolves the full absolute path, collapsing any
    # ../ sequences in the process. For example:
    # "../../../etc/passwd" becomes "C:\etc\passwd" on Windows.
    # We then check that the resolved path still starts where we expect.
    resolved = os.path.abspath(filepath)

    # Get the absolute path of the current working directory.
    # The file must be at or below this directory — not above it.
    cwd = os.path.abspath(os.getcwd())

    # commonpath() finds the shared root of two paths.
    # If resolved starts with cwd, they share the same root — safe.
    # If resolved escapes above cwd (e.g. via ../), the common path
    # will be shorter than cwd — that's a traversal attempt.
    try:
        common = os.path.commonpath([resolved, cwd])
    except ValueError:
        # ValueError is raised on Windows when paths are on different drives.
        # A cross-drive path is automatically unsafe.
        masLog(f"File path validation failed: '{filepath}' is on a different drive", level="warning")
        return False

    if common != cwd:
        masLog(f"File path validation failed: '{filepath}' attempts path traversal", level="warning")
        return False

    # Check that the file actually exists on disk.
    if not os.path.isfile(resolved):
        masLog(f"File path validation failed: '{filepath}' does not exist", level="warning")
        return False

    # Check that the file extension is .html or .htm.
    # os.path.splitext() splits "index.html" into ("index", ".html").
    _, ext = os.path.splitext(resolved)
    if ext.lower() not in (".html", ".htm"):
        masLog(f"File path validation failed: '{filepath}' is not an HTML file", level="warning")
        return False

    masLog(f"File path validation passed: '{resolved}'")
    return True