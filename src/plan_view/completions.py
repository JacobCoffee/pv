"""Shell tab completion for the pv CLI."""

import argparse
import sys
from pathlib import Path

from plan_view.commands.edit import _list_restore_points
from plan_view.formatting import VALID_STATUSES
from plan_view.io import load_plan, resolve_plan_path
from plan_view.state import get_all_phase_ids, get_all_task_ids

# Fields accepted by `pv set <id> <field> <value>`
SET_FIELDS = ("status", "agent", "skill", "title", "files", "research", "plan")

# Types accepted by `pv rm <type> <id>`
RM_TYPES = ("phase", "task")

# Modes accepted by `--ai <mode>`
AI_MODES = ("context", "actionable")

# All commands with (name, aliases, description)
_COMMANDS = [
    ("current", "c", "Show current phase and active tasks"),
    ("next", "n", "Show next actionable task"),
    ("phase", "p", "Show current phase details"),
    ("get", "g", "Get task details by ID"),
    ("last", "l", "Show recently completed tasks"),
    ("future", "f", "Show upcoming tasks"),
    ("summary", "s", "Show plan summary"),
    ("table", "t", "Show task table for a phase"),
    ("bugs", "b", "Show bug tasks"),
    ("deferred", "d", "Show deferred tasks"),
    ("ideas", "i", "Show idea tasks"),
    ("validate", "v", "Validate plan against schema"),
    ("files", "", "Show files for a task"),
    ("help", "h", "Show help text"),
    ("init", "", "Initialize a new plan"),
    ("add-phase", "", "Add a new phase"),
    ("add-task", "", "Add a task to a phase"),
    ("set", "", "Set a task field"),
    ("done", "", "Mark task as completed"),
    ("start", "", "Mark task as in_progress"),
    ("block", "", "Mark task as blocked"),
    ("skip", "", "Mark task as skipped"),
    ("defer", "", "Move task to deferred"),
    ("bug", "", "Move task to bugs"),
    ("idea", "", "Move task to ideas"),
    ("rm", "", "Remove a phase or task"),
    ("compact", "", "Compact backup files"),
    ("restore", "", "Restore from backup"),
    ("reconcile", "", "Reconcile plan progress"),
    ("dashboard", "", "Launch web dashboard"),
    ("completion", "", "Print shell completion script"),
]

# Commands that take a task ID as first positional arg
_TASK_ID_COMMANDS = {"done", "start", "block", "skip", "defer", "bug", "idea", "get", "g", "files", "set"}

# Commands that take a phase ID as first positional arg
_PHASE_ID_COMMANDS = {"add-task", "table", "t"}


def cmd_complete(args: argparse.Namespace) -> None:
    """Output completion values, one per line. Hidden subcommand for shell scripts."""
    completion_type = args.completion_type
    try:
        if completion_type == "task-ids":
            plan_path = resolve_plan_path(getattr(args, "file", None))
            plan = load_plan(plan_path)
            if plan is None:
                return
            for task_id, _title, _phase in get_all_task_ids(plan, limit=99999):
                print(task_id)

        elif completion_type == "phase-ids":
            plan_path = resolve_plan_path(getattr(args, "file", None))
            plan = load_plan(plan_path)
            if plan is None:
                return
            for phase_id, _name in get_all_phase_ids(plan):
                print(phase_id)

        elif completion_type == "restore-points":
            backup_dir = Path(".claude/plan-view")
            if not backup_dir.exists():
                return
            points = _list_restore_points(backup_dir)
            for idx, _pt in enumerate(points, 1):
                print(idx)

        elif completion_type == "statuses":
            for s in VALID_STATUSES:
                print(s)

        elif completion_type == "set-fields":
            for f in SET_FIELDS:
                print(f)

        elif completion_type == "rm-types":
            for t in RM_TYPES:
                print(t)

        elif completion_type == "ai-modes":
            for m in AI_MODES:
                print(m)

    except Exception:  # noqa: BLE001, S110
        pass  # Completions must never error


_USAGE_HINTS = {
    "bash": (
        '# Temporary:  eval "$(pv completion bash)"\n'
        "# Permanent:  pv completion bash > ~/.local/share/bash-completion/completions/pv\n"
    ),
    "zsh": (
        '# Temporary:  eval "$(pv completion zsh)"\n'
        "# Permanent:  pv completion zsh > ~/.zfunc/_pv  (ensure fpath includes ~/.zfunc)\n"
    ),
    "fish": (
        "# Temporary:  pv completion fish | source\n"
        "# Permanent:  pv completion fish > ~/.config/fish/completions/pv.fish\n"
    ),
}


def cmd_completion(args: argparse.Namespace) -> None:
    """Print shell completion script to stdout."""
    shell = args.shell
    hint = _USAGE_HINTS.get(shell, "")
    if shell == "bash":
        print(hint + _bash_completion())
    elif shell == "zsh":
        print(hint + _zsh_completion())
    elif shell == "fish":
        print(hint + _fish_completion())
    else:
        print(f"Unknown shell: {shell}", file=sys.stderr)
        sys.exit(1)


def _all_command_names() -> list[str]:
    """Return flat list of all command names and aliases."""
    names = []
    for name, alias, _desc in _COMMANDS:
        names.append(name)
        if alias:
            names.append(alias)
    return names


def _bash_completion() -> str:
    """Generate bash completion script."""
    cmds = " ".join(_all_command_names())

    return f"""\
# bash completion for pv
_pv() {{
    local cur prev words cword
    _init_completion || return

    local commands="{cmds}"

    # Global flags
    if [[ "$cur" == -* ]]; then
        COMPREPLY=( $(compgen -W "-f --file --json --ai -h --help -a --all" -- "$cur") )
        return
    fi

    # Find the subcommand
    local cmd=""
    local cmd_idx=0
    for ((i=1; i < cword; i++)); do
        case "${{words[i]}}" in
            -f|--file) ((i++)); continue ;;
            --json|--ai|-h|--help|-a|--all) continue ;;
            -*) continue ;;
            *)
                cmd="${{words[i]}}"
                cmd_idx=$i
                break
                ;;
        esac
    done

    # No subcommand yet — complete commands
    if [[ -z "$cmd" ]]; then
        COMPREPLY=( $(compgen -W "$commands" -- "$cur") )
        return
    fi

    local pos=$((cword - cmd_idx))

    # Per-command completions
    case "$cmd" in
        {"|".join(sorted(_TASK_ID_COMMANDS))})
            if [[ $pos -eq 1 ]]; then
                COMPREPLY=( $(compgen -W "$(pv _complete task-ids 2>/dev/null)" -- "$cur") )
            fi
            ;;
        {"|".join(sorted(_PHASE_ID_COMMANDS))})
            if [[ $pos -eq 1 ]]; then
                COMPREPLY=( $(compgen -W "$(pv _complete phase-ids 2>/dev/null)" -- "$cur") )
            fi
            ;;
        set)
            case $pos in
                1) COMPREPLY=( $(compgen -W "$(pv _complete task-ids 2>/dev/null)" -- "$cur") ) ;;
                2) COMPREPLY=( $(compgen -W "$(pv _complete set-fields 2>/dev/null)" -- "$cur") ) ;;
                3)
                    if [[ "$prev" == "status" ]]; then
                        COMPREPLY=( $(compgen -W "$(pv _complete statuses 2>/dev/null)" -- "$cur") )
                    fi
                    ;;
            esac
            ;;
        rm)
            case $pos in
                1) COMPREPLY=( $(compgen -W "$(pv _complete rm-types 2>/dev/null)" -- "$cur") ) ;;
                2)
                    if [[ "$prev" == "phase" ]]; then
                        COMPREPLY=( $(compgen -W "$(pv _complete phase-ids 2>/dev/null)" -- "$cur") )
                    elif [[ "$prev" == "task" ]]; then
                        COMPREPLY=( $(compgen -W "$(pv _complete task-ids 2>/dev/null)" -- "$cur") )
                    fi
                    ;;
            esac
            ;;
        restore)
            if [[ $pos -eq 1 ]]; then
                COMPREPLY=( $(compgen -W "$(pv _complete restore-points 2>/dev/null)" -- "$cur") )
            fi
            ;;
        completion)
            if [[ $pos -eq 1 ]]; then
                COMPREPLY=( $(compgen -W "bash zsh fish" -- "$cur") )
            fi
            ;;
    esac

    # Per-command flags
    if [[ "$cur" == -* ]]; then
        case "$cmd" in
            init)           COMPREPLY=( $(compgen -W "--force -q --quiet -d --dry-run" -- "$cur") ) ;;
            add-phase)      COMPREPLY=( $(compgen -W "--desc -q --quiet -d --dry-run" -- "$cur") ) ;;
            add-task)       COMPREPLY=( $(compgen -W "--agent --skill --deps --files -q -d" -- "$cur") ) ;;
            set|done|start|block|skip|bug|idea)
                            COMPREPLY=( $(compgen -W "-q --quiet -d --dry-run" -- "$cur") ) ;;
            defer)          COMPREPLY=( $(compgen -W "-r --reason -q --quiet -d --dry-run" -- "$cur") ) ;;
            rm)             COMPREPLY=( $(compgen -W "-q --quiet -d --dry-run" -- "$cur") ) ;;
            compact)        COMPREPLY=( $(compgen -W "-n --max-backups -q --quiet -d --dry-run" -- "$cur") ) ;;
            restore)        COMPREPLY=( $(compgen -W "-q --quiet -d --dry-run" -- "$cur") ) ;;
            reconcile)      COMPREPLY=( $(compgen -W "-q --quiet -d --dry-run --json" -- "$cur") ) ;;
            last|future)    COMPREPLY=( $(compgen -W "-n --count -a --all --json" -- "$cur") ) ;;
            dashboard)      COMPREPLY=( $(compgen -W "-p --port" -- "$cur") ) ;;
            *)              COMPREPLY=( $(compgen -W "--json" -- "$cur") ) ;;
        esac
    fi
}}

complete -F _pv pv"""


def _zsh_completion() -> str:
    """Generate zsh completion script."""
    # Build command descriptions for _describe
    cmd_lines = []
    for name, alias, desc in _COMMANDS:
        cmd_lines.append(f"        '{name}:{desc}'")
        if alias:
            cmd_lines.append(f"        '{alias}:{desc}'")
    cmd_array = "\n".join(cmd_lines)

    task_id_cmds = "|".join(sorted(_TASK_ID_COMMANDS))
    phase_id_cmds = "|".join(sorted(_PHASE_ID_COMMANDS))

    return f'''\
#compdef pv
# zsh completion for pv

_pv() {{
    local -a commands
    commands=(
{cmd_array}
    )

    _arguments -C \\
        '-f[Plan file]:file:_files -g "*.json"' \\
        '--file[Plan file]:file:_files -g "*.json"' \\
        '--json[Output as JSON]' \\
        '--ai[AI output mode]:mode:(context actionable)' \\
        '-h[Show help]' \\
        '--help[Show help]' \\
        '-a[Show all]' \\
        '--all[Show all]' \\
        '1:command:->cmd' \\
        '*::arg:->args'

    case $state in
        cmd)
            _describe 'command' commands
            ;;
        args)
            case $words[1] in
                {task_id_cmds})
                    local -a task_ids
                    task_ids=(${{(f)"$(pv _complete task-ids 2>/dev/null)"}})
                    _describe 'task' task_ids
                    ;;
                {phase_id_cmds})
                    local -a phase_ids
                    phase_ids=(${{(f)"$(pv _complete phase-ids 2>/dev/null)"}})
                    _describe 'phase' phase_ids
                    ;;
                set)
                    case $CURRENT in
                        2)
                            local -a task_ids
                            task_ids=(${{(f)"$(pv _complete task-ids 2>/dev/null)"}})
                            _describe 'task' task_ids
                            ;;
                        3)
                            local -a fields
                            fields=(${{(f)"$(pv _complete set-fields 2>/dev/null)"}})
                            _describe 'field' fields
                            ;;
                        4)
                            if [[ "$words[3]" == "status" ]]; then
                                local -a statuses
                                statuses=(${{(f)"$(pv _complete statuses 2>/dev/null)"}})
                                _describe 'status' statuses
                            fi
                            ;;
                    esac
                    ;;
                rm)
                    case $CURRENT in
                        2)
                            _describe 'type' '(phase task)'
                            ;;
                        3)
                            if [[ "$words[2]" == "phase" ]]; then
                                local -a phase_ids
                                phase_ids=(${{(f)"$(pv _complete phase-ids 2>/dev/null)"}})
                                _describe 'phase' phase_ids
                            elif [[ "$words[2]" == "task" ]]; then
                                local -a task_ids
                                task_ids=(${{(f)"$(pv _complete task-ids 2>/dev/null)"}})
                                _describe 'task' task_ids
                            fi
                            ;;
                    esac
                    ;;
                restore)
                    local -a points
                    points=(${{(f)"$(pv _complete restore-points 2>/dev/null)"}})
                    _describe 'restore point' points
                    ;;
                completion)
                    _describe 'shell' '(bash zsh fish)'
                    ;;
            esac
            ;;
    esac
}}

_pv "$@"'''


def _fish_completion() -> str:
    """Generate fish completion script."""
    lines = [
        "# fish completion for pv",
        "",
        "# Disable file completion by default",
        "complete -c pv -f",
        "",
        "# Global flags",
        'complete -c pv -n "__fish_use_subcommand" -s f -l file -r -F -d "Plan file"',
        'complete -c pv -n "__fish_use_subcommand" -l json -d "Output as JSON"',
        'complete -c pv -n "__fish_use_subcommand" -l ai -r -d "AI output mode"',
        'complete -c pv -n "__fish_use_subcommand" -s h -l help -d "Show help"',
        'complete -c pv -n "__fish_use_subcommand" -s a -l all -d "Show all"',
        "",
        "# Commands",
    ]

    for name, alias, desc in _COMMANDS:
        lines.append(f'complete -c pv -n "__fish_use_subcommand" -a "{name}" -d "{desc}"')
        if alias:
            lines.append(f'complete -c pv -n "__fish_use_subcommand" -a "{alias}" -d "{desc}"')

    lines.append("")
    lines.append("# Dynamic completions for task ID commands")
    lines.extend(
        f'complete -c pv -n "__fish_seen_subcommand_from {cmd}" '
        f'-a "(pv _complete task-ids 2>/dev/null)" -d "Task ID"'
        for cmd in sorted(_TASK_ID_COMMANDS)
    )

    lines.append("")
    lines.append("# Dynamic completions for phase ID commands")
    lines.extend(
        f'complete -c pv -n "__fish_seen_subcommand_from {cmd}" '
        f'-a "(pv _complete phase-ids 2>/dev/null)" -d "Phase ID"'
        for cmd in sorted(_PHASE_ID_COMMANDS)
    )

    lines.extend([
        "",
        "# rm type completions",
        'complete -c pv -n "__fish_seen_subcommand_from rm" -a "phase task" -d "Type"',
        "",
        "# restore point completions",
        'complete -c pv -n "__fish_seen_subcommand_from restore" '
        '-a "(pv _complete restore-points 2>/dev/null)" -d "Restore point"',
        "",
        "# completion shell completions",
        'complete -c pv -n "__fish_seen_subcommand_from completion" -a "bash zsh fish" -d "Shell"',
        "",
        "# AI mode completions",
        'complete -c pv -l ai -a "context actionable" -d "AI mode"',
    ])

    return "\n".join(lines)
