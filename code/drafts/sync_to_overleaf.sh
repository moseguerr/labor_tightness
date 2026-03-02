#!/bin/bash
# Render .qmd files and push .tex output to Overleaf clones
# Usage: ./code/drafts/sync_to_overleaf.sh [--no-render] [--dry-run] [--target syp|diss|both]
#
# Targets:
#   syp  = Second Year Paper Overleaf (Main/Current Draft.tex)
#   diss = Dissertation Overleaf (chapter 3.tex)
#   both = Both (default)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DRAFTS_DIR="$(cd "$SCRIPT_DIR/../../drafts" && pwd)"

# Detect Dropbox
if [ -n "${DROPBOX_HOME:-}" ]; then
  DROPBOX="$DROPBOX_HOME"
elif [ -d "$HOME/Library/CloudStorage/Dropbox" ]; then
  DROPBOX="$HOME/Library/CloudStorage/Dropbox"
elif [ -d "$HOME/Dropbox" ]; then
  DROPBOX="$HOME/Dropbox"
else
  echo "ERROR: Dropbox folder not found." >&2
  exit 1
fi

OVERLEAF_SYP="$DROPBOX/labor_tightness/drafts/overleaf"
OVERLEAF_DISS="$DROPBOX/labor_tightness/drafts/overleaf-dissertation"
NO_RENDER=false
DRY_RUN=false
TARGET="both"

for arg in "$@"; do
  case "$arg" in
    --no-render)   NO_RENDER=true ;;
    --dry-run)     DRY_RUN=true ;;
    --target=*)    TARGET="${arg#--target=}" ;;
  esac
done

# Step 1: Render (unless --no-render)
if [ "$NO_RENDER" = false ]; then
  echo "=== Step 1: Rendering .qmd -> .tex ==="
  quarto render "$DRAFTS_DIR/main.qmd" --to pdf
  echo "Render complete."
else
  echo "=== Skipping render (--no-render) ==="
fi

TEX_FILE="$DRAFTS_DIR/_output/main.tex"
if [ ! -f "$TEX_FILE" ]; then
  echo "ERROR: $TEX_FILE not found. Run without --no-render first." >&2
  exit 1
fi

# Step 2: Sync to Second Year Paper Overleaf
if [ "$TARGET" = "syp" ] || [ "$TARGET" = "both" ]; then
  echo ""
  echo "=== Step 2a: Syncing to Second Year Paper Overleaf ==="

  if [ "$DRY_RUN" = true ]; then
    echo "[DRY RUN] Would copy: $TEX_FILE -> $OVERLEAF_SYP/Main/Current Draft.tex"
    echo "[DRY RUN] Would copy: bibliography.bib"
    echo "[DRY RUN] Would rsync: figures/ -> Figures/"
  else
    cp "$TEX_FILE" "$OVERLEAF_SYP/Main/Current Draft.tex"
    if [ -f "$DRAFTS_DIR/bibliography.bib" ]; then
      cp "$DRAFTS_DIR/bibliography.bib" "$OVERLEAF_SYP/Main/bibliography.bib"
    fi
    # Sync figures (note case difference: local figures/ -> Overleaf Figures/)
    if [ -d "$DRAFTS_DIR/figures/" ] && [ "$(ls -A "$DRAFTS_DIR/figures/" 2>/dev/null)" ]; then
      rsync -av --delete "$DRAFTS_DIR/figures/" "$OVERLEAF_SYP/Figures/" --exclude '.DS_Store'
    fi
    echo "Files copied to Second Year Paper."

    # Commit and push
    cd "$OVERLEAF_SYP"
    git add -A
    if git diff --cached --quiet; then
      echo "No changes to push to SYP."
    else
      git commit -m "Sync from Quarto source $(date +%Y-%m-%d_%H:%M)"
      git push origin master
      echo "Pushed to Second Year Paper Overleaf."
    fi
  fi
fi

# Step 3: Sync to Dissertation Overleaf
if [ "$TARGET" = "diss" ] || [ "$TARGET" = "both" ]; then
  echo ""
  echo "=== Step 2b: Syncing to Dissertation Overleaf ==="

  if [ "$DRY_RUN" = true ]; then
    echo "[DRY RUN] Would copy: $TEX_FILE -> $OVERLEAF_DISS/chapter 3.tex"
    echo "[DRY RUN] Would rsync: figures/ -> Graphs_1/"
  else
    cp "$TEX_FILE" "$OVERLEAF_DISS/chapter 3.tex"
    # Sync figures to Graphs_1/
    if [ -d "$DRAFTS_DIR/figures/" ] && [ "$(ls -A "$DRAFTS_DIR/figures/" 2>/dev/null)" ]; then
      rsync -av --delete "$DRAFTS_DIR/figures/" "$OVERLEAF_DISS/Graphs_1/" --exclude '.DS_Store'
    fi
    echo "Files copied to Dissertation."

    # Commit and push
    cd "$OVERLEAF_DISS"
    git add -A
    if git diff --cached --quiet; then
      echo "No changes to push to Dissertation."
    else
      git commit -m "Sync ch3 from Quarto source $(date +%Y-%m-%d_%H:%M)"
      git push origin master
      echo "Pushed to Dissertation Overleaf."
    fi
  fi
fi

echo ""
echo "Done."
