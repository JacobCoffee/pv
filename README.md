# pv - Plan Viewer

Pretty print `plan.json` for AI agent task tracking.

## Installation

```bash
# Global install with uv
uv tool install git+https://github.com/JacobCoffee/pv

# Or from local checkout
uv tool install /path/to/pv
```

## Usage

```bash
pv                  # Full plan overview
pv next             # Show next pending/in-progress task
pv current          # Completed summary + current phase + next task
pv phase            # Current phase with all tasks + dependencies
pv validate         # Validate plan.json against schema
pv help             # Show help

# Use a different file
pv current other.json
```

## Example Output

```
📋 Shortlist App v1.0.0
Progress: 15% (9/60 tasks)

✅ Phase 0: Project Foundation (100%)

🔄 Phase 1: Core Data Models & Authentication (11%)
   Implement user system with buyer/researcher roles and authentication

   ✅ [1.1.1] Create User model (python-backend-engineer)
   ⏳ [1.1.2] Create ResearcherProfile model (python-backend-engineer)
   ⏳ [1.1.3] Create ResearchRequest model (python-backend-engineer)

👉 Next: [1.1.2] Create ResearcherProfile model
```

## Plan Schema

See [plan.schema.json](https://github.com/JacobCoffee/shortlist-app/blob/main/.claude/config/plan.schema.json) for the full schema specification.

## License

MIT
