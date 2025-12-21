"""CLI for viewing and editing plan.json files."""

import argparse
import sys
from pathlib import Path

from plan_view.commands.edit import (
    cmd_add_phase,
    cmd_add_task,
    cmd_block,
    cmd_bug,
    cmd_defer,
    cmd_done,
    cmd_init,
    cmd_rm,
    cmd_set,
    cmd_skip,
    cmd_start,
)
from plan_view.commands.view import (
    HELP_TEXT,
    cmd_bugs,
    cmd_current,
    cmd_deferred,
    cmd_get,
    cmd_last,
    cmd_next,
    cmd_overview,
    cmd_phase,
    cmd_summary,
    cmd_validate,
)

# Re-export all public API for backward compatibility with tests
from plan_view.formatting import (
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
    green,
    now_iso,
)
from plan_view.io import load_plan, load_schema, save_plan
from plan_view.state import (
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
    "cmd_summary",
    "cmd_bugs",
    "cmd_deferred",
    "cmd_validate",
    # Edit Commands
    "cmd_init",
    "cmd_add_phase",
    "cmd_add_task",
    "cmd_set",
    "cmd_done",
    "cmd_start",
    "cmd_block",
    "cmd_skip",
    "cmd_defer",
    "cmd_bug",
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
    last_p.add_argument("-a", "--all", action="store_true")
    last_p.add_argument("--json", action="store_true", default=None)

    summary_p = subparsers.add_parser("summary", aliases=["s"], add_help=False)
    summary_p.add_argument("--json", action="store_true", default=None)

    bugs_p = subparsers.add_parser("bugs", aliases=["b"], add_help=False)
    bugs_p.add_argument("--json", action="store_true", default=None)

    deferred_p = subparsers.add_parser("deferred", aliases=["d"], add_help=False)
    deferred_p.add_argument("--json", action="store_true", default=None)

    subparsers.add_parser("help", aliases=["h"], add_help=False)

    # Init
    init_p = subparsers.add_parser("init", add_help=False)
    init_p.add_argument("name")
    init_p.add_argument("--force", action="store_true")
    init_p.add_argument("-q", "--quiet", action="store_true")
    init_p.add_argument("-d", "--dry-run", action="store_true")

    # Add phase
    add_phase_p = subparsers.add_parser("add-phase", add_help=False)
    add_phase_p.add_argument("name")
    add_phase_p.add_argument("--desc")
    add_phase_p.add_argument("-q", "--quiet", action="store_true")
    add_phase_p.add_argument("-d", "--dry-run", action="store_true")

    # Add task
    add_task_p = subparsers.add_parser("add-task", add_help=False)
    add_task_p.add_argument("phase")
    add_task_p.add_argument("title")
    add_task_p.add_argument("--agent")
    add_task_p.add_argument("--deps")
    add_task_p.add_argument("-q", "--quiet", action="store_true")
    add_task_p.add_argument("-d", "--dry-run", action="store_true")

    # Set field
    set_p = subparsers.add_parser("set", add_help=False)
    set_p.add_argument("id")
    set_p.add_argument("field")
    set_p.add_argument("value")
    set_p.add_argument("-q", "--quiet", action="store_true")
    set_p.add_argument("-d", "--dry-run", action="store_true")

    # Shortcuts
    done_p = subparsers.add_parser("done", add_help=False)
    done_p.add_argument("id")
    done_p.add_argument("-q", "--quiet", action="store_true")
    done_p.add_argument("-d", "--dry-run", action="store_true")

    start_p = subparsers.add_parser("start", add_help=False)
    start_p.add_argument("id")
    start_p.add_argument("-q", "--quiet", action="store_true")
    start_p.add_argument("-d", "--dry-run", action="store_true")

    block_p = subparsers.add_parser("block", add_help=False)
    block_p.add_argument("id")
    block_p.add_argument("-q", "--quiet", action="store_true")
    block_p.add_argument("-d", "--dry-run", action="store_true")

    skip_p = subparsers.add_parser("skip", add_help=False)
    skip_p.add_argument("id")
    skip_p.add_argument("-q", "--quiet", action="store_true")
    skip_p.add_argument("-d", "--dry-run", action="store_true")

    defer_p = subparsers.add_parser("defer", add_help=False)
    defer_p.add_argument("id")
    defer_p.add_argument("-q", "--quiet", action="store_true")
    defer_p.add_argument("-d", "--dry-run", action="store_true")

    bug_p = subparsers.add_parser("bug", add_help=False)
    bug_p.add_argument("id")
    bug_p.add_argument("-q", "--quiet", action="store_true")
    bug_p.add_argument("-d", "--dry-run", action="store_true")

    # Remove
    rm_p = subparsers.add_parser("rm", add_help=False)
    rm_p.add_argument("type", choices=["phase", "task"])
    rm_p.add_argument("id")
    rm_p.add_argument("-q", "--quiet", action="store_true")
    rm_p.add_argument("-d", "--dry-run", action="store_true")

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
        case "block":
            cmd_block(args)
            return
        case "skip":
            cmd_skip(args)
            return
        case "defer":
            cmd_defer(args)
            return
        case "bug":
            cmd_bug(args)
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
            cmd_last(plan, None if args.all else args.count, as_json=as_json)
        case "summary" | "s":
            cmd_summary(plan, as_json=as_json)
        case "bugs" | "b":
            cmd_bugs(plan, as_json=as_json)
        case "deferred" | "d":
            cmd_deferred(plan, as_json=as_json)
        case "validate" | "v":
            cmd_validate(plan, args.file, as_json=as_json)
        case _:
            cmd_overview(plan, as_json=as_json)


if __name__ == "__main__":
    main()
