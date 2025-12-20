"""CLI for viewing and editing plan.json files."""

import argparse
import sys
from pathlib import Path

from pv_tool.commands.edit import (
    cmd_add_phase,
    cmd_add_task,
    cmd_done,
    cmd_init,
    cmd_rm,
    cmd_set,
    cmd_start,
)
from pv_tool.commands.view import (
    HELP_TEXT,
    cmd_current,
    cmd_get,
    cmd_last,
    cmd_next,
    cmd_overview,
    cmd_phase,
    cmd_validate,
)

# Re-export all public API for backward compatibility with tests
from pv_tool.formatting import (
    BOLD,
    CYAN,
    DIM,
    GREEN,
    ICONS,
    RESET,
    VALID_STATUSES,
    YELLOW,
    bold,
    bold_cyan,
    bold_yellow,
    dim,
    get_status_icon,
    green,
    now_iso,
)
from pv_tool.io import load_plan, load_schema, save_plan
from pv_tool.state import (
    find_phase,
    find_task,
    get_current_phase,
    get_next_task,
    recalculate_progress,
    task_to_dict,
)

# Explicit __all__ for documentation and IDE support
__all__ = [
    # Constants
    "ICONS",
    "VALID_STATUSES",
    "RESET",
    "BOLD",
    "DIM",
    "GREEN",
    "YELLOW",
    "CYAN",
    "HELP_TEXT",
    # Formatting
    "bold",
    "dim",
    "green",
    "bold_cyan",
    "bold_yellow",
    "now_iso",
    "get_status_icon",
    # I/O
    "load_plan",
    "save_plan",
    "load_schema",
    # State
    "recalculate_progress",
    "get_current_phase",
    "get_next_task",
    "find_task",
    "find_phase",
    "task_to_dict",
    # View Commands
    "cmd_overview",
    "cmd_current",
    "cmd_next",
    "cmd_phase",
    "cmd_get",
    "cmd_last",
    "cmd_validate",
    # Edit Commands
    "cmd_init",
    "cmd_add_phase",
    "cmd_add_task",
    "cmd_set",
    "cmd_done",
    "cmd_start",
    "cmd_rm",
    # Entry point
    "main",
]


def main() -> None:
    """CLI entry point for pv command."""
    parser = argparse.ArgumentParser(
        prog="pv",
        description="View and edit plan.json for task tracking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        usage="pv [-f FILE] [--json] <command> [args]",
        add_help=False,
    )
    parser.add_argument(
        "-f",
        "--file",
        type=Path,
        default=Path("plan.json"),
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        help=argparse.SUPPRESS,
    )

    subparsers = parser.add_subparsers(dest="command", metavar="command")

    # View commands (all support --json, default=None to not override parent)
    for name, aliases in [("current", ["c"]), ("next", ["n"]), ("phase", ["p"]), ("validate", ["v"])]:
        sp = subparsers.add_parser(name, aliases=aliases, add_help=False, parents=[])
        sp.add_argument("--json", action="store_true", default=None)

    get_p = subparsers.add_parser("get", aliases=["g"], add_help=False)
    get_p.add_argument("id")
    get_p.add_argument("--json", action="store_true", default=None)

    last_p = subparsers.add_parser("last", aliases=["l"], add_help=False)
    last_p.add_argument("-n", "--count", type=int, default=5)
    last_p.add_argument("--json", action="store_true", default=None)

    subparsers.add_parser("help", aliases=["h"], add_help=False)

    # Init
    init_p = subparsers.add_parser("init", add_help=False)
    init_p.add_argument("name")
    init_p.add_argument("--force", action="store_true")

    # Add phase
    add_phase_p = subparsers.add_parser("add-phase", add_help=False)
    add_phase_p.add_argument("name")
    add_phase_p.add_argument("--desc")

    # Add task
    add_task_p = subparsers.add_parser("add-task", add_help=False)
    add_task_p.add_argument("phase")
    add_task_p.add_argument("title")
    add_task_p.add_argument("--agent")
    add_task_p.add_argument("--deps")

    # Set field
    set_p = subparsers.add_parser("set", add_help=False)
    set_p.add_argument("id")
    set_p.add_argument("field")
    set_p.add_argument("value")

    # Shortcuts
    done_p = subparsers.add_parser("done", add_help=False)
    done_p.add_argument("id")

    start_p = subparsers.add_parser("start", add_help=False)
    start_p.add_argument("id")

    # Remove
    rm_p = subparsers.add_parser("rm", add_help=False)
    rm_p.add_argument("type", choices=["phase", "task"])
    rm_p.add_argument("id")

    args = parser.parse_args()

    # Help command
    if args.help or args.command in ("help", "h"):
        print(HELP_TEXT)
        return

    # Handle edit commands that don't need to load plan first
    match args.command:
        case "init":
            cmd_init(args)
            return
        case "add-phase":
            cmd_add_phase(args)
            return
        case "add-task":
            cmd_add_task(args)
            return
        case "set":
            cmd_set(args)
            return
        case "done":
            cmd_done(args)
            return
        case "start":
            cmd_start(args)
            return
        case "rm":
            cmd_rm(args)
            return

    # View commands need to load plan
    plan = load_plan(args.file)
    if plan is None:
        sys.exit(1)
    assert plan is not None  # Help type checker after sys.exit

    # --json can appear anywhere in args
    as_json = "--json" in sys.argv

    match args.command:
        case "current" | "c":
            cmd_current(plan, as_json=as_json)
        case "next" | "n":
            cmd_next(plan, as_json=as_json)
        case "phase" | "p":
            cmd_phase(plan, as_json=as_json)
        case "get" | "g":
            cmd_get(plan, args.id, as_json=as_json)
        case "last" | "l":
            cmd_last(plan, args.count, as_json=as_json)
        case "validate" | "v":
            cmd_validate(plan, args.file, as_json=as_json)
        case _:
            cmd_overview(plan, as_json=as_json)


if __name__ == "__main__":
    main()
