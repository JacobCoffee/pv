"""ANSI terminal formatting utilities for pv-tool."""

from datetime import UTC, datetime

# Status icons
ICONS = {
    "completed": "✅",
    "in_progress": "🔄",
    "pending": "⏳",
    "blocked": "🛑",
    "skipped": "⏭️",
}

VALID_STATUSES = ("pending", "in_progress", "completed", "blocked", "skipped")

# ANSI colors
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"


def bold(text: str) -> str:
    """Apply bold ANSI formatting to text."""
    return f"{BOLD}{text}{RESET}"


def dim(text: str) -> str:
    """Apply dim ANSI formatting to text."""
    return f"{DIM}{text}{RESET}"


def green(text: str) -> str:
    """Apply green ANSI color to text."""
    return f"{GREEN}{text}{RESET}"


def bold_cyan(text: str) -> str:
    """Apply bold cyan ANSI formatting to text."""
    return f"{BOLD}{CYAN}{text}{RESET}"


def bold_yellow(text: str) -> str:
    """Apply bold yellow ANSI formatting to text."""
    return f"{BOLD}{YELLOW}{text}{RESET}"


def now_iso() -> str:
    """Return current UTC time in ISO 8601 format."""
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def get_status_icon(status: str) -> str:
    """Return emoji icon for a task status."""
    return ICONS.get(status, "❓")
