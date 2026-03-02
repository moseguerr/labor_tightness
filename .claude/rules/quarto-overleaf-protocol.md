# Quarto-Overleaf Sync Protocol

## Overleaf Projects

This project has two Overleaf projects:
- **Second Year Paper** (standalone): `62fa64e2aba0c236c0fd5fb6` → `drafts/overleaf/`
- **Dissertation** (chapter 3 = latest): `67ad3b7dcba37e66662a2796` → `drafts/overleaf-dissertation/`

Both are cloned in Dropbox at `~/Library/CloudStorage/Dropbox/labor_tightness/drafts/`.

## Source of Truth

The `.qmd` files in `drafts/` are the **single source of truth** for all written content.
The Overleaf clones are MIRRORs — never edit them directly unless a coauthor does.

## Directory Mapping

### Second Year Paper
| Local (Git) | Overleaf (Dropbox) |
|---|---|
| `drafts/figures/` | `overleaf/Figures/` |
| `drafts/_output/main.tex` | `overleaf/Main/Current Draft.tex` |
| `drafts/bibliography.bib` | `overleaf/Main/bibliography.bib` |

### Dissertation (Chapter 3)
| Local (Git) | Overleaf (Dropbox) |
|---|---|
| `drafts/figures/` | `overleaf-dissertation/Graphs_1/` |
| `drafts/_output/main.tex` | `overleaf-dissertation/chapter 3.tex` |

## Sync Rules

1. **Edit only `.qmd` files.** Never edit `.tex` output or the Overleaf clone directly.
2. **Render before syncing:** Always run `render_all.sh` before `sync_to_overleaf.sh`.
3. **Pull before pushing:** If coauthors may have edited Overleaf, run `pull_from_overleaf.sh` first.
4. **Backport manually:** Coauthor prose edits in Overleaf `.tex` must be manually applied to `.qmd` sources.

## Commands

```bash
./code/drafts/render_all.sh          # Render all .qmd to PDF
./code/drafts/sync_to_overleaf.sh    # Render + push to Overleaf
./code/drafts/pull_from_overleaf.sh  # Pull + diff coauthor changes
```
