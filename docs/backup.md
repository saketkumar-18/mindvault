# Backup Guide

MindVault stores everything locally under `MV_HOME` (default `~/.mindvault`).
Backing up is a simple file copy — no cloud service required.

## What to back up

| Item | Location |
|---|---|
| SQLite database | `{MV_HOME}/mindvault.db` |
| Uploaded documents | `{MV_HOME}/documents/` |
| Vector index | `{MV_HOME}/index/` |
| Configuration | `.env` (if you created one) + your settings (in the DB) |

## Recommended procedure

1. Stop the MindVault process (or at least avoid uploading/indexing while copying).
2. Copy the four items above to your backup medium (external drive, NAS, etc.).

Example (PowerShell):

```powershell
# Stop MindVault, then:
Copy-Item -Recurse "$HOME\.mindvault" "D:\backups\mindvault-2026-01-01"
```

Example (Linux/macOS):

```bash
tar -czf mindvault-backup-$(date +%F).tar.gz -C "$HOME" .mindvault
```

> Tip: the `.npz` vector index is regenerable — the vector store can be rebuilt
> from the SQLite chunk text (re-index documents). If you must choose what to
> back up, keep `mindvault.db` and `documents/` first.

## Restoring

1. Stop MindVault.
2. Replace `{MV_HOME}` with your backup.
3. Start MindVault.

## Data export

You can also export conversations and knowledge-base metadata as JSON from
**Settings → Export Data** (or via `GET /api/export/all`), which works without
touching the filesystem.
