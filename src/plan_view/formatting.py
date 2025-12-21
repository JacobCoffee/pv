"""ANSI terminal formatting utilities for pv-tool."""

import os
import sys
from datetime import UTC, datetime

# Status icons
ICONS = {
    "completed": "✅",
    "in_progress": "🔄",
    "pending": "⏳",
    "blocked": "🛑",
    "skipped": "⏭️",
}

VALID_STATUSES = tuple(ICONS)

# ANSI colors
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"


def _use_color() -> bool:
    """Determine if color output should be used.

    Follows the NO_COLOR standard (https://no-color.org/):
    - NO_COLOR env var (any value) disables color
    - FORCE_COLOR env var (any value) forces color even in pipes
    - Otherwise, color is enabled only if stdout is a TTY
    """
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return sys.stdout.isatty()


def bold(text: str) -> str:
    """Apply bold ANSI formatting to text."""
    if not _use_color():
        return text
    return f"{BOLD}{text}{RESET}"


def dim(text: str) -> str:
    """Apply dim ANSI formatting to text."""
    if not _use_color():
        return text
    return f"{DIM}{text}{RESET}"


def green(text: str) -> str:
    """Apply green ANSI color to text."""
    if not _use_color():
        return text
    return f"{GREEN}{text}{RESET}"


def bold_cyan(text: str) -> str:
    """Apply bold cyan ANSI formatting to text."""
    if not _use_color():
        return text
    return f"{BOLD}{CYAN}{text}{RESET}"


def bold_yellow(text: str) -> str:
    """Apply bold yellow ANSI formatting to text."""
    if not _use_color():
        return text
    return f"{BOLD}{YELLOW}{text}{RESET}"


def now_iso() -> str:
    """Return current UTC time in ISO 8601 format."""
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
