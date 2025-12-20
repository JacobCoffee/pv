# pv - Plan Viewer

Pretty print and edit `plan.json` for task tracking.

## Installation

```bash
# Global install with uv
uv tool install git+https://github.com/JacobCoffee/pv

# Or from local checkout
uv tool install /path/to/pv
```

## Usage

### View Commands

```bash
pv                  # Full plan overview
pv current          # Completed summary + current phase + next task
pv next             # Show next pending/in-progress task
pv phase            # Current phase with all tasks + dependencies
pv validate         # Validate plan.json against schema
```

### Edit Commands

```bash
pv init "Project Name"                    # Create new plan.json
pv add-phase "Auth" --desc "User auth"    # Add a phase
pv add-task 1 "Create model" --agent X    # Add task to phase 1
pv start 1.1.1                            # Mark task in_progress
pv done 1.1.1                             # Mark task completed
pv set 1.1.1 status blocked               # Set any status
pv set 1.1.1 agent python-backend-engineer
pv rm task 1.1.1                          # Remove a task
pv rm phase 2                             # Remove a phase
```

### Options

```bash
pv -f other.json current    # Use different file
pv init "Name" --force      # Overwrite existing plan.json
```

## Example

```bash
$ pv init "My App"
✅ Created plan.json for 'My App'

$ pv add-phase "Setup" --desc "Project setup"
✅ Added Phase 0: Setup

$ pv add-task 0 "Initialize repo" --agent github-git-expert
✅ Added [0.1.1] Initialize repo

$ pv done 0.1.1
✅ [0.1.1] status → completed

$ pv current
📋 My App v1.0.0
Progress: 100% (1/1 tasks)

✅ Phase 0: Setup (100%)
```

## Features

- Auto-calculates progress percentages
- Updates phase status based on task completion
- Tracks `started_at` and `completed_at` timestamps
- Validates against plan.json schema

## License

MIT
