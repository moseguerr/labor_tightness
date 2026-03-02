#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────
# setup_split.sh — Split labor_tightness into Code (GitHub) + Data (Dropbox)
#
# Code repo:  ~/Repositories/labor_tightness
# Data store: ~/Library/CloudStorage/Dropbox/labor_tightness
#
# Run from repo root:  bash setup_split.sh
# Fix symlinks only:   bash setup_split.sh --fix-symlinks
# ──────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Argument parsing ──────────────────────────────────────────────
FIX_ONLY=false
if [ "${1:-}" = "--fix-symlinks" ]; then
    FIX_ONLY=true
fi

# ── Paths ─────────────────────────────────────────────────────────
REPO_DIR="$HOME/Repositories/labor_tightness"

# ── Step 0: Detect Dropbox root ───────────────────────────────────
detect_dropbox() {
    if [ -n "${DROPBOX_HOME:-}" ]; then
        echo "$DROPBOX_HOME"
    elif [ -d "$HOME/Library/CloudStorage/Dropbox" ]; then
        echo "$HOME/Library/CloudStorage/Dropbox"
    elif [ -d "$HOME/Dropbox" ]; then
        echo "$HOME/Dropbox"
    else
        echo "ERROR: Dropbox folder not found." >&2
        echo "  Set DROPBOX_HOME in your shell profile to override." >&2
        return 1
    fi
}

DROPBOX_ROOT="$(detect_dropbox)" || exit 1
DROPBOX_DIR="$DROPBOX_ROOT/labor_tightness"

# Directories that should live in Dropbox and be symlinked from repo
DATA_DIRS=(
    "data"          # intermediate data files (Dropbox-sized, not TB-scale)
    "logs"          # processing logs, run records
    "notes"         # paper drafts, literature, IRB, presentations
    "secrets"       # any credentials or API keys
)

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Labor Tightness: Code/Data Split Setup                    ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Code repo  → $REPO_DIR"
echo "║  Data store → $DROPBOX_DIR"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ── Step 1: Ensure repo directory exists ──────────────────────────
if ! $FIX_ONLY; then
    if [ -d "$REPO_DIR/.git" ]; then
        echo "✓ Repo already exists at $REPO_DIR"
    elif [ -d "$REPO_DIR" ]; then
        echo "⚠ Directory exists but is not a git repo: $REPO_DIR"
        echo "  Initializing..."
        cd "$REPO_DIR"
        git init
        echo "✓ Repo initialized"
    else
        echo "→ Creating repo directory at $REPO_DIR..."
        mkdir -p "$REPO_DIR"
        cd "$REPO_DIR"
        git init
        echo "✓ Repo created and initialized"
    fi
fi

# ── Step 2: Ensure Dropbox data directories exist ─────────────────
echo ""
echo "→ Ensuring Dropbox data directories exist..."
for dir in "${DATA_DIRS[@]}"; do
    mkdir -p "$DROPBOX_DIR/$dir"
    echo "  ✓ $DROPBOX_DIR/$dir"
done

# ── Step 3: Move data FROM repo TO Dropbox (if it exists in repo) ─
if ! $FIX_ONLY; then
    echo ""
    echo "→ Migrating data directories from repo to Dropbox (if present)..."
    for dir in "${DATA_DIRS[@]}"; do
        if [ -d "$REPO_DIR/$dir" ] && [ ! -L "$REPO_DIR/$dir" ]; then
            echo "  Moving $dir/ contents to Dropbox..."
            rsync -a --ignore-existing "$REPO_DIR/$dir/" "$DROPBOX_DIR/$dir/"
            rm -rf "$REPO_DIR/$dir"
            echo "  ✓ $dir/ migrated"
        elif [ -L "$REPO_DIR/$dir" ]; then
            echo "  ✓ $dir/ already symlinked"
        else
            echo "  · $dir/ not present in repo (OK)"
        fi
    done
fi

# ── Step 4: Create symlinks from repo → Dropbox ──────────────────
echo ""
echo "→ Creating symlinks from repo → Dropbox..."
for dir in "${DATA_DIRS[@]}"; do
    target="$DROPBOX_DIR/$dir"
    link="$REPO_DIR/$dir"
    if [ -L "$link" ] && [ ! -e "$link" ]; then
        echo "  ⚠ Broken symlink: $dir/ → fixing..."
        rm "$link"
        ln -s "$target" "$link"
        echo "  ✓ $dir/ → $target (fixed)"
    elif [ -L "$link" ]; then
        echo "  ✓ $dir/ → already linked"
    else
        ln -s "$target" "$link"
        echo "  ✓ $dir/ → $target"
    fi
done

# ── Step 5: Update .gitignore ─────────────────────────────────────
if ! $FIX_ONLY; then
    echo ""
    echo "→ Ensuring .gitignore is up to date..."
    GITIGNORE="$REPO_DIR/.gitignore"
    if [ ! -f "$GITIGNORE" ]; then
        cat > "$GITIGNORE" << 'GITIGNORE'
# ── Symlinked directories (live in Dropbox) ──
data/
logs/
notes/
secrets/

# ── Large data files (live on external drive / server) ──
*.dta
*.parquet
*.csv
*.csv.zip
*.zip
*.xlsx
*.xls

# ── OS ──
.DS_Store
Thumbs.db

# ── Python ──
__pycache__/
*.pyc
*.pyo
.venv/
venv/
.env

# ── R ──
.Rhistory
.RData
.Rproj.user/

# ── Output files ──
*.pdf
*.png
*.jpg
*.jpeg

# ── Temp ──
/tmp/
GITIGNORE
        echo "  ✓ .gitignore created"
    else
        echo "  ✓ .gitignore already exists"
    fi
fi

# ── Done ──────────────────────────────────────────────────────────
echo ""
if $FIX_ONLY; then
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║  ✅ Symlink repair complete!                               ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
else
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║  ✅ Setup complete!                                        ║"
    echo "╠══════════════════════════════════════════════════════════════╣"
    echo "║                                                            ║"
    echo "║  Repo (code):    ~/Repositories/labor_tightness            ║"
    echo "║  Dropbox (data): $DROPBOX_DIR"
    echo "║                                                            ║"
    echo "║  Symlinks in repo:                                         ║"
    echo "║    data/    → Dropbox (intermediate data)                  ║"
    echo "║    logs/    → Dropbox (processing logs)                    ║"
    echo "║    notes/   → Dropbox (paper, literature, IRB)             ║"
    echo "║    secrets/ → Dropbox (credentials)                        ║"
    echo "║                                                            ║"
    echo "║  NOTE: Raw data (TB-scale) stays on external drive/server  ║"
    echo "║    External: /Volumes/Expansion/All server/                ║"
    echo "║    Server:   /global/home/pc_moseguera/data/               ║"
    echo "║                                                            ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
fi
