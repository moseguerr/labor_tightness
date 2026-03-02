---
paths:
  - "**/*.py"
  - "**/*.R"
---

# Quality Gates & Scoring Rubrics

## Thresholds

- **80/100 = Commit** -- good enough to save
- **90/100 = PR** -- ready for review
- **95/100 = Excellence** -- aspirational

## Python Scripts (.py)

| Severity | Issue | Deduction |
|----------|-------|-----------|
| Critical | Syntax errors | -100 |
| Critical | Security issue (exposed secrets, injection) | -30 |
| Critical | Hardcoded absolute paths | -20 |
| Critical | Missing error handling on file/network I/O | -15 |
| Major | Missing type hints on public functions | -5 |
| Major | Unused imports | -2 |
| Major | Missing docstrings on public functions | -3 |
| Minor | Line length > 100 chars | -1 |
| Minor | print() instead of logging in production code | -1 |

## R Scripts (.R)

| Severity | Issue | Deduction |
|----------|-------|-----------|
| Critical | Syntax errors | -100 |
| Critical | Hardcoded absolute paths | -20 |
| Critical | Missing library() calls for used packages | -15 |
| Major | No comments on regression specifications | -5 |
| Major | Unused variables | -2 |
| Minor | Line length > 100 chars | -1 |

## Data Pipelines

| Severity | Issue | Deduction |
|----------|-------|-----------|
| Critical | Non-reproducible (missing random seed) | -30 |
| Critical | No data validation on input | -20 |
| Critical | Hardcoded file paths | -20 |
| Major | No logging of data shape/summary | -10 |
| Major | Missing intermediate checkpoints | -5 |
| Major | No error handling on API calls | -10 |
| Minor | Missing progress indicators for long operations | -2 |

## Enforcement

- **Score < 80:** Block commit. List blocking issues.
- **Score < 90:** Allow commit, warn. List recommendations.
- User can override with justification.

## Quality Reports

Generated **only at merge time**. Use `templates/quality-report.md` for format.
Save to `quality_reports/merges/YYYY-MM-DD_[branch-name].md`.
