# Organizational Purpose as a Costly Signal in Tight Labor Markets

## Research Question

Do firms use **organizational purpose claims** in job postings as costly signals or cheap substitutes for compensation when competing for talent in tight labor markets?

The paper finds that firms making purpose claims in competitive markets offer ~4% higher wages — consistent with costly signaling, not substitution.

## The Construct

The focal construct is **organizational purpose and the meaningful work it promises** — not broad "social responsibility." Three elements:
1. **Stated organizational purpose** — mission beyond profit ("mission-driven," "sustainable world")
2. **Meaningful work promised by that purpose** — employee-facing promise ("make a real difference," "lasting impact")
3. **Identity/ideology alignment signals** — ("shared values," "passion for impact")

**Excluded:** Good-employer signals (career development, work-life balance), task-level occupational meaning, pecuniary benefits.

See `notes/PROJECT_OVERVIEW.md` for full construct details, theoretical framing, and dictionary category breakdown.

## Split-Storage Architecture

Code in Git (`~/Repositories/labor_tightness/`), everything else in Dropbox via symlinks.

| Folder | Location | Contents |
|--------|----------|----------|
| `code/` | Git repo | Python data cleaning + R regressions |
| `code/defunct/` | Git repo | Older-generation scripts (Jan 2023), kept for reference |
| `data/` | Dropbox symlink | Intermediate data files (Dropbox-sized) |
| `logs/` | Dropbox symlink | Processing logs, run records |
| `notes/` | Dropbox symlink | Paper drafts, literature, IRB, presentations, project overview |
| `secrets/` | Dropbox symlink | Credentials, API keys |

**Raw data (TB-scale)** — too large for Dropbox:
- External drive: `/Volumes/Expansion/All server/`
- Georgetown server: `/global/home/pc_moseguera/data/Burning Glass 2/`

Run `bash setup_split.sh` to recreate symlinks. Use `--fix-symlinks` to repair.

## Data

- **Lightcast (Burning Glass)** — ~21M U.S. job postings (2010-2021), ~70% of online openings
- **Compustat** — Firm financials (profitability, size, leverage, Tobin's Q, ROE)
- **BLS LAUS** — MSA-level unemployment rates (quarterly)
- **OEWS** — Occupation-level employment growth
- **ACS** — Occupation-level age distribution
- **EPA NAICS** — High-polluting industry identification
- **Auxiliary** — GDP, industry employment/productivity, JOLTS, educational attainment, demographics

Sample: 4,040 firms, 21.5M posts (full); 3,464 firms, 4.9M posts (wage subsample).

## Code Structure

### `code/data_clean/` — Python pipeline (runs on Georgetown server)

| File | Purpose |
|------|---------|
| `xml_to_dataframe.py` | Parse raw XML job posting feeds |
| `SingleMain.py` | Process individual monthly CSV files |
| `main.py` | Core processing orchestrator |
| `mergeMain.py` | Merge processed monthly datasets |
| `mergeOther.py` | Merge auxiliary data sources |
| `AggYear.py` | Year-level aggregation |
| `AggFull.py` | Full dataset aggregation (2010-2023) |
| `textProcess.py` | NLP processing of job descriptions |
| `skillProcess.py` | Extract and classify skills |
| `get_final_variables.py` | Compute analytical variables |
| `refine_dictionaries.py` | Dictionary expansion via KeyBERT + SentenceTransformers |
| `call_*.py` | Orchestrator scripts for batch processing |
| `debugg*.py` | Debug versions of pipeline scripts |
| `construct_bartik.py` | Bartik shift-share IV instrument (BHJ 2022) |
| `construct_bartik_robustness.py` | Alternative baseline (2007) + state LOO variants |
| `bartik_diagnostics.py` | Core IV diagnostics (effective N, F-stat, Rotemberg, balance) |
| `bartik_diagnostics_fixes.py` | JRS dynamic, change spec, no-611 fix variants |
| `bartik_covariate_balance.py` | Bai-style covariate balance on MSA demographics |
| `bartik_ssaggregate.py` | BHJ exposure-robust SEs (ssaggregate) |
| `process_qcew_2022_2025.py` | Download/process QCEW data through 2025 Q2 |

Server paths:
- Input: `/global/home/pc_moseguera/data/Burning Glass 2/`
- Output: `/global/home/pc_moseguera/data/Burning Glass 2/merged_variables/`

### `code/regressions/` — R regression analysis

Root level:
- `wages_main_*.R` — Primary wage regressions with purpose claim × tightness interactions
- `wages_mean_*.R` — Mean wage specifications
- `wages_precov_*.R` — Pre-COVID period (2010-2019)
- `wages_quarter_*.R` — Quarterly variation
- `wages_age_*.R`, `wages_education_*.R` — Demographic heterogeneity
- `wages_decomposed_skills_*.R` — Skill decomposition
- `unemp_reg*.R` — Unemployment regressions (Analysis 1)
- `Table3_*.R`, `Table4_*.R` — Final publication tables
- `wages_iv_bartik.R` — Full IV regression suite (first stage, 2SLS, JRS, Oster)

Subfolders:
- `firm_level/prosocial_main/` — Firm-level unemployment regressions (by quartile, MSA, year)
- `firm_level/secondary_analysis/` — Continuous measures + pre-COVID firm analysis
- `job_level/wage_main/` — Job-level wage regressions (base, MSA, year)
- `job_level/secondary_analysis/` — Age, occupational growth, pre-COVID, continuous
- `job_level/full_sample/` — Full sample job-level regressions

### `code/defunct/` — Archived older scripts

Older-generation scripts from Jan 2023 (pre-construct-refinement). Kept for reference, not actively used.

## Key Variables

- `main_strict_ind` — Organizational purpose claims indicator (strict definition)
- `below25_unemp` — Below 25th percentile MSA unemployment rate (tightest markets)
- `above75_emp` — Above 75th percentile employment growth
- `log_sal` — Log minimum advertised salary (primary outcome)
- `log_length` — Log job posting length
- `log_num_skills` — Log number of required skills

**Key R packages:** `lfe` (fixed effects), `estimatr`, `haven` (Stata), `texreg` (tables), `dplyr`, `lubridate`

## Empirical Strategy

- **Analysis 1:** Purpose claims ~ labor market tightness (firm × MSA × occupation × quarter)
- **Analysis 2:** Log wages ~ purpose claims × tightness (job post level)
- **Identification:** Within-firm variation in MSA-level unemployment; Bartik shift-share IV (BHJ 2022 framework, exposure-robust SEs)
- **Fixed effects:** Firm, occupation×industry×year, MSA, specialized skills proportion

## Current Status

- Full empirical analysis complete; all main tables and robustness checks produced
- **Bartik IV:** Instrument constructed, diagnostics complete, robustness variants built, exposure-robust SEs computed. IV R scripts ready — need to run on Georgetown server.
- **In progress:** Construct narrowing (SR → organizational purpose), framing revision
- **Next:** Run IV regressions on server, dictionary revision + re-run, IV results tables, rewrite intro/theory, submit (AMJ/SMJ/OS)
- **Lab studies:** Two studies under IRB prep at Georgetown (dictionary validation + credibility mechanism)

## Notion

- Project page: https://www.notion.so/2f407b592ad380acb14ff3c706bf8707
- Central database: https://www.notion.so/00ec152aa791439f8817422147dcfc6e

## File Naming Convention

R regression files use date suffixes (MMDD): `wages_main_0308.R` = March 8th version.

## Notes Structure (Dropbox)

```
notes/
  PROJECT_OVERVIEW.md    — Full project knowledge document
  drafts/                — Paper drafts, appendix, methods TeX
  literature/            — 29 research papers + EmeraldInsight collection
  presentations/         — LaTeX slides (Proposal June 2022, Temporal)
  irb/                   — IRB protocols, consent forms, study materials
  data_admin/            — Data sharing agreements, Burning Glass dictionary
```

## Original Locations (for reference)

- **Second YPP (Dropbox):** `~/Library/CloudStorage/Dropbox/Second YPP/` — original project folder
- **External drive:** `/Volumes/Expansion/All server/` — 1.7TB raw + processed data
- **Server:** `/global/home/pc_moseguera/data/Burning Glass 2/`
