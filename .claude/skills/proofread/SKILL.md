---
name: proofread
description: Run proofreading on draft files. Checks grammar, typos, consistency, and academic writing quality. Produces a report without editing files.
argument-hint: "[filename or 'all']"
allowed-tools: ["Read", "Grep", "Glob", "Write", "Task"]
---

# Proofread Draft Files

Run the proofreading protocol on research paper drafts. This produces a report of all issues found WITHOUT editing any source files.

## Steps

1. **Identify files to review:**
   - If `$ARGUMENTS` is a specific filename: review that file only
   - If `$ARGUMENTS` is "all": review all draft files in `drafts/`

2. **For each file, check for:**

   **GRAMMAR:** Subject-verb agreement, articles (a/an/the), prepositions, tense consistency
   **TYPOS:** Misspellings, search-and-replace artifacts, duplicated words
   **CONSISTENCY:** Citation format, notation, terminology across sections
   **ACADEMIC QUALITY:** Informal language, missing words, awkward constructions
   **LATEX/QUARTO:** Broken cross-references, malformed math environments, undefined commands in raw LaTeX blocks

3. **Produce a detailed report** for each file listing every finding with:
   - Location (line number or section heading)
   - Current text (what's wrong)
   - Proposed fix (what it should be)
   - Category and severity

4. **Save each report** to `quality_reports/`:
   - `quality_reports/FILENAME_proofread_report.md`

5. **IMPORTANT: Do NOT edit any source files.**
   Only produce the report. Fixes are applied separately after user review.

6. **Present summary** to the user:
   - Total issues found per file
   - Breakdown by category
   - Most critical issues highlighted

## Files to scan:
```
drafts/*.qmd
drafts/*.tex
```
