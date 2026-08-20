# Git / GitHub Workflow

## Branching

| Branch | Purpose |
|--------|---------|
| `main` | Stable, phase-complete work |
| `phase/N-short-name` | Work for a single phase (optional) |
| `fix/...` / `feat/...` | Small focused changes |

## Daily workflow

1. Pull latest `main` (once remote exists)
2. Work on the current phase only
3. Commit with clear messages (what/why)
4. Push and open a PR when a phase is ready for review (optional)

## Commit message style

```
phase1: create monorepo foundation and docs
phase2: add dataset acquisition scripts
```

## What not to commit

- `.env` / secrets
- `data/raw/**`, `data/processed/**` (except tiny placeholders / `.gitkeep`)
- `ml/models/**` weights/checkpoints
- `node_modules/`, `__pycache__/`, build outputs

## Phase gate

Do not start the next phase until the current phase’s acceptance criteria are confirmed.
