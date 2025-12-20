# Quickstart

Get up and running with pv in under a minute.

## Installation

Install pv globally using uv:

```bash
uv tool install git+https://github.com/JacobCoffee/pv
```

Or via pip:

```bash
pip install pv-tool
```

## Create Your First Plan

Initialize a new plan.json:

```bash
pv init "My Project"
```

This creates a `plan.json` file in your current directory with the basic structure:

```json
{
  "meta": {
    "project": "My Project",
    "version": "1.0.0",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  "summary": {
    "total_phases": 0,
    "total_tasks": 0,
    "completed_tasks": 0,
    "overall_progress": 0
  },
  "phases": []
}
```

## Add Phases and Tasks

Add a phase to organize your work:

```bash
pv add-phase "Setup" --desc "Project initialization tasks"
```

Add tasks to the phase:

```bash
pv add-task 0 "Create repository" --agent github-git-expert
pv add-task 0 "Set up CI/CD" --agent github-git-expert
pv add-task 0 "Configure linting" --agent coder
```

## Track Progress

Start working on a task:

```bash
pv start 0.1.1
```

Mark it complete:

```bash
pv done 0.1.1
```

## View Your Plan

See the full overview:

```bash
pv
```

```
📋 My Project v1.0.0
Progress: 33% (1/3 tasks)

🔄 Phase 0: Setup (33%)
   Project initialization tasks

   ✅ [0.1.1] Create repository (github-git-expert)
   ⏳ [0.1.2] Set up CI/CD (github-git-expert)
   ⏳ [0.1.3] Configure linting (coder)
```

## What's Next?

- Check out the [CLI Reference](cli.md) for all available commands
- Learn about the [Plan Schema](schema.md) for advanced usage
- Use `pv --json` for machine-readable output in scripts
