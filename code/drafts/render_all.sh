#!/bin/bash
# Render all .qmd files to PDF
# Usage: ./code/drafts/render_all.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DRAFTS_DIR="$(cd "$SCRIPT_DIR/../../drafts" && pwd)"

echo "=== Rendering main.qmd ==="
quarto render "$DRAFTS_DIR/main.qmd" --to pdf

echo ""
echo "=== Render complete ==="
echo "Output: $DRAFTS_DIR/_output/"
ls -la "$DRAFTS_DIR/_output/" 2>/dev/null || echo "(no output files yet)"
