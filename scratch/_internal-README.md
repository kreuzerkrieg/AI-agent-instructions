# _internal — agent working area

> **Canonical source:** this file is tracked in the AI-agent-instructions repo at
> `scratch/_internal-README.md` and seeded into
> `~/.config/JetBrains/CLion2026.1/scratches/GitHubCopilot/_internal/README.md`.
> If this local copy is absent or older than the repo template, re-copy it from the repo.
> Do **not** put machine-specific content here — keep that in `INVENTORY.md` (local, untracked).

This directory is the **agent's private scratch space**. Nothing here is meant for the user.
The parent directory (`../`) is reserved for user-facing reports/documents.

Keep here: helper scripts, follow-up notes, intermediate data, and **slim log snapshots**
(logs only — never copy full `testlog/` data dirs; they are hundreds of GB).

## Cleanup policy
`_internal/` is disposable. Scrub anything no longer needed. Delete a snapshot/script once its
analysis is finalized into a user-facing report in `../`. Periodically prune items that are
100% obsolete. When in doubt, keep — but don't let it grow unbounded.

## Inventory
Machine-specific item tracking lives in **`INVENTORY.md`** (local, not tracked in the repo).
Maintain it as a short table: each item, its purpose, and when it's safe to delete — so future
sessions can prune confidently.

