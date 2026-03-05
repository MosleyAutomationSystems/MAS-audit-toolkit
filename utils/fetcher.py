# utils/fetcher.py
# Responsible for loading HTML content from either a URL or a local file.
# This is the only module in the toolkit that performs network requests
# or reads files from disk. Everything else receives HTML as a string.
import truststore
truststore.inject_into_ssl()
import requests
import certifi
import os

import config
from utils.logger import masLog
from utils.validator import validate_url, validate_filepath

def fetch_from_url(url: str) -> str | None:
    """
    Fetch the HTML content of a webpage by URL.

    Parameters:
        url (str): A validated http:// or https:// URL.

    Returns:
        str: The raw HTML content of the page, or None if the request failed.
    """

    # Log that we are about to make a network request.
    masLog(f"Fetching URL: {url}")

    try:
        # requests.get() sends an HTTP GET request to the URL.
        # timeout= prevents the tool from hanging indefinitely on slow servers.
        # headers= sends our User-Agent string so servers don't block us as a bot.
        # Both values come from config.py — no magic numbers here.
        response = requests.get(
            url,
            timeout=config.REQUEST_TIMEOUT,
            headers=config.REQUEST_HEADERS,
            verify=certifi.where()
        )

        # raise_for_status() checks the HTTP response code.
        # If the server returned 404, 500, or any error code, this raises
        # an HTTPError exception rather than silently returning bad content.
        response.raise_for_status()

        masLog(f"Successfully fetched URL: {url} (status {response.status_code})")

        # response.text returns the page content decoded as a string.
        return response.text

    except requests.exceptions.Timeout:
        # The server took longer than REQUEST_TIMEOUT seconds to respond.
        masLog(f"Request timed out for URL: {url}", level="error")
        return None

    except requests.exceptions.HTTPError as e:
        # The server responded but with an error status code (4xx or 5xx).
        masLog(f"HTTP error for URL: {url} — {e}", level="error")
        return None

    except requests.exceptions.RequestException as e:
        # Catch-all for any other network error (DNS failure, no connection, etc.)
        masLog(f"Network error for URL: {url} — {e}", level="error")
        return None


def fetch_from_file(filepath: str) -> str | None:
    """
    Load HTML content from a local file.

    Parameters:
        filepath (str): A validated path to a local .html or .htm file.

    Returns:
        str: The raw HTML content of the file, or None if reading failed.
    """

    # Resolve the absolute path before reading.
    resolved = os.path.abspath(filepath)

    masLog(f"Reading local file: {resolved}")

    try:
        # Open the file in read mode with UTF-8 encoding.
        # UTF-8 is the standard encoding for HTML files.
        # encoding="utf-8" prevents crashes on files with special characters.
        # errors="replace" substitutes a placeholder for any unreadable bytes
        # rather than crashing — tolerant of imperfect real-world files.
        with open(resolved, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        masLog(f"Successfully read local file: {resolved}")
        return content

    except OSError as e:
        # OSError covers file not found, permission denied, and other OS-level errors.
        masLog(f"Failed to read local file: {resolved} — {e}", level="error")
        return None


def load_html(source: str) -> str | None:
    """
    Master loader — determines whether source is a URL or file path,
    validates it, and routes it to the correct fetch function.

    Parameters:
        source (str): Either a URL or a local file path supplied by the user.

    Returns:
        str: Raw HTML content, or None if validation or loading failed.
    """

    # If the source starts with http:// or https://, treat it as a URL.
    if source.strip().lower().startswith("http"):
        if not validate_url(source):
            masLog(f"Aborting load — URL failed validation: {source}", level="error")
            return None
        return fetch_from_url(source)

    # Otherwise treat it as a local file path.
    else:
        if not validate_filepath(source):
            masLog(f"Aborting load — file path failed validation: {source}", level="error")
            return None
        return fetch_from_file(source)