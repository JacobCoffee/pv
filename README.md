# pv

A command-line tool for viewing and editing `plan.json` task tracking files.

## Installation

```bash
uv tool install plan-view
```

## Quick Start

```bash
# Create a new plan
pv init "My Project"

# Add phases and tasks
pv add-phase "Setup" --desc "Initial configuration"
pv add-task 0 "Initialize repository" --agent github-git-expert

# Track progress
pv start 0.1.1
pv done 0.1.1

# View status
pv current
```

## Commands

### View

| Command | Description |
|---------|-------------|
| `pv` | Full plan overview |
| `pv current` | Current phase and next task |
| `pv next` | Next actionable task |
| `pv phase` | Current phase details |
| `pv get <id>` | Show task or phase by ID |
| `pv last` | Recently completed tasks |
| `pv summary` | Progress summary |
| `pv bugs` | Show bugs phase |
| `pv deferred` | Show deferred phase |
| `pv validate` | Validate against schema |

### Edit

| Command | Description |
|---------|-------------|
| `pv init <name>` | Create new plan.json |
| `pv add-phase <name>` | Add a phase |
| `pv add-task <phase> <title>` | Add a task |
| `pv done <id>` | Mark completed |
| `pv start <id>` | Mark in progress |
| `pv block <id>` | Mark blocked |
| `pv skip <id>` | Mark skipped |
| `pv defer <id>` | Move to deferred |
| `pv bug <id>` | Move to bugs |
| `pv set <id> <field> <value>` | Set task field |
| `pv rm task <id>` | Remove task |
| `pv rm phase <id>` | Remove phase |

### Options

| Option | Description |
|--------|-------------|
| `-f, --file` | Specify plan file path |
| `--json` | JSON output (view commands) |
| `-q, --quiet` | Suppress output (edit commands) |
| `-d, --dry-run` | Preview changes without saving |

## Example Output

```
$ pv -f examples/simple.json current

API Backend v1.0.0
Progress: 40% (2/5 tasks)

Phase 0: Setup (100%)
Phase 1: Core Features (0%)
   Create user authentication
   Build REST API endpoints

Next: [1.1.1] Create user authentication
```

## JSON Output

All view commands support `--json` for programmatic access:

```bash
$ pv next --json
{
  "id": "1.1.1",
  "title": "Create user authentication",
  "status": "in_progress",
  "phase_id": "1",
  "phase_name": "Core Features",
  "agent_type": "python-backend-engineer",
  "depends_on": ["0.1.2"]
}
```

## Features

- Automatic progress calculation
- Dependency-aware task ordering
- Partial task ID matching (`pv done 1` matches `1.1.1` if unique)
- Schema validation
- NO_COLOR/FORCE_COLOR environment variable support
- Dry-run mode for previewing changes

## Documentation

See the [full documentation](https://jacobcoffee.github.io/pv/) for detailed usage.

## License

MIT
