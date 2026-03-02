# Split-Storage Protocol

**Code in Git, data in Dropbox.** Connected via symlinks at the repo root.

## Standard Symlinks

| Symlink | Contents |
|---------|----------|
| `data/` | Intermediate data files (Dropbox-sized, not TB-scale) |
| `secrets/` | API keys, credentials, `.env` files, tokens |
| `notes/` | Paper drafts, literature, IRB, presentations, project overview |
| `logs/` | Processing logs, run outputs |

**TB-scale data** stays on external drive (`/Volumes/Expansion/All server/`) or Georgetown server (`/global/home/pc_moseguera/data/Burning Glass 2/`).

## Rules

1. **Never create** `data/`, `secrets/`, `notes/`, or `logs/` as regular directories — they are symlinks. If they don't exist, run `bash setup_split.sh`.
2. **Never hardcode** a Dropbox path. Use `$DROPBOX_HOME` or the `detect_dropbox` function.
3. **Never commit** anything inside symlinked directories to Git.
4. **Never hardcode** secrets in source files. Read from `secrets/` or environment variables.
5. **Write logs** to `logs/`, not to the repo root or source directories.
6. **Research notes** go in `notes/`, not alongside code.
7. **Data files** (CSVs, parquets, Stata files) go in `data/` or stay on external storage.
8. Use **relative paths** (`data/`, `secrets/`, etc.) so symlinks resolve transparently.

## Dropbox Detection

Resolution order (used in `setup_split.sh`):
1. `$DROPBOX_HOME` environment variable
2. `$HOME/Library/CloudStorage/Dropbox` (modern macOS)
3. `$HOME/Dropbox` (legacy / Linux)
