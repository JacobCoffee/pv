# Quickstart

Get started with pv in under a minute.

## Installation

`````{tab-set}
````{tab-item} uv (recommended)
```bash
uv tool install plan-view
```
````

````{tab-item} pip
```bash
pip install plan-view
```
````

````{tab-item} pipx
```bash
pipx install plan-view
```
````
`````

## Create a Plan

Initialize a new plan.json:

```bash
pv init "My Project"
```

Output:

```
Created plan.json for 'My Project'
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
pv add-task 0 "Configure linting"
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

See the current status:

```bash
pv current
```

Output:

```
My Project v1.0.0
Progress: 33% (1/3 tasks)

Phase 0: Setup (33%)
   Project initialization tasks

   [0.1.1] Create repository (github-git-expert)
   [0.1.2] Set up CI/CD (github-git-expert)
   [0.1.3] Configure linting

Next: [0.1.2] Set up CI/CD
```

## Using the Examples

The repository includes example plan files. Try them:

```bash
# View a simple project plan
pv -f examples/simple.json

# Check the next task
pv -f examples/simple.json next

# View a more complex project
pv -f examples/complex.json current
```

## Next Steps

- See the [CLI Reference](cli.md) for all available commands
- Learn about the [Plan Schema](schema.md) for the file structure
- Use `pv --json` for machine-readable output in scripts
