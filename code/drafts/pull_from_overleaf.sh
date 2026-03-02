#!/bin/bash
# Pull latest from Overleaf and show diff against last rendered .tex
# Usage: ./code/drafts/pull_from_overleaf.sh [--target syp|diss|both]

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
TARGET="both"

for arg in "$@"; do
  case "$arg" in
    --target=*) TARGET="${arg#--target=}" ;;
  esac
done

RENDERED_TEX="$DRAFTS_DIR/_output/main.tex"

# Pull Second Year Paper
if [ "$TARGET" = "syp" ] || [ "$TARGET" = "both" ]; then
  echo "=== Pulling from Second Year Paper Overleaf ==="
  cd "$OVERLEAF_SYP"
  git pull origin master
  echo ""

  echo "=== SYP Manuscript diff ==="
  OVERLEAF_TEX="$OVERLEAF_SYP/Main/Current Draft.tex"

  if [ ! -f "$RENDERED_TEX" ]; then
    echo "WARNING: No rendered .tex found at $RENDERED_TEX"
    echo "Run render_all.sh first to create a baseline."
  else
    echo "Overleaf version: $OVERLEAF_TEX"
    echo "Last rendered:    $RENDERED_TEX"
    echo ""

    DIFF_OUTPUT=$(diff --unified=3 "$RENDERED_TEX" "$OVERLEAF_TEX" || true)

    if [ -z "$DIFF_OUTPUT" ]; then
      echo "No differences found. Overleaf matches last render."
    else
      echo "$DIFF_OUTPUT"
      echo ""
      echo "=== Summary ==="
      ADDITIONS=$(echo "$DIFF_OUTPUT" | grep -c '^+[^+]' || true)
      DELETIONS=$(echo "$DIFF_OUTPUT" | grep -c '^-[^-]' || true)
      echo "Lines added in Overleaf: $ADDITIONS"
      echo "Lines removed in Overleaf: $DELETIONS"
    fi
  fi
  echo ""
fi

# Pull Dissertation
if [ "$TARGET" = "diss" ] || [ "$TARGET" = "both" ]; then
  echo "=== Pulling from Dissertation Overleaf ==="
  cd "$OVERLEAF_DISS"
  git pull origin master
  echo ""

  echo "=== Dissertation ch3 diff ==="
  DISS_TEX="$OVERLEAF_DISS/chapter 3.tex"

  if [ ! -f "$RENDERED_TEX" ]; then
    echo "WARNING: No rendered .tex found at $RENDERED_TEX"
  elif [ -f "$DISS_TEX" ]; then
    DIFF_OUTPUT=$(diff --unified=3 "$RENDERED_TEX" "$DISS_TEX" || true)
    if [ -z "$DIFF_OUTPUT" ]; then
      echo "No differences found."
    else
      ADDITIONS=$(echo "$DIFF_OUTPUT" | grep -c '^+[^+]' || true)
      DELETIONS=$(echo "$DIFF_OUTPUT" | grep -c '^-[^-]' || true)
      echo "Lines changed: +$ADDITIONS / -$DELETIONS"
    fi
  fi
  echo ""
fi

# Check bibliography changes
echo "=== Bibliography diff ==="
LOCAL_BIB="$DRAFTS_DIR/bibliography.bib"
OVERLEAF_BIB="$OVERLEAF_SYP/Main/bibliography.bib"

if [ -f "$LOCAL_BIB" ] && [ -f "$OVERLEAF_BIB" ]; then
  BIB_DIFF=$(diff --unified=3 "$LOCAL_BIB" "$OVERLEAF_BIB" || true)
  if [ -z "$BIB_DIFF" ]; then
    echo "Bibliography unchanged."
  else
    echo "Bibliography has changes:"
    echo "$BIB_DIFF" | head -30
  fi
else
  echo "WARNING: Local or Overleaf bibliography not found."
fi

echo ""
echo "=== Next Steps ==="
echo "  1. Review the diffs above"
echo "  2. Backport relevant prose edits to drafts/main.qmd"
echo "  3. Run: ./code/drafts/render_all.sh"
echo "  4. Run: ./code/drafts/sync_to_overleaf.sh"
echo ""
echo "Done."
