# Orchestrator Report — Study 2 Modifications + Study 1 Phrase Refinement

**Date:** 2026-03-03
**Scope:** Study 2 restructuring (4 stages, wage visibility, competition), prewritten employer branding sections for Study 3, expanded bucket sort

---

## Inventory Findings

### What Existed at Start

- 5 posting files (A-E): complete, with Stage 1 (wages hidden) and Stage 2 (wages revealed) versions
- Study 2 design summary: complete but with 2-stage structure and no wage visibility between-subjects factor
- Ranking task screens: 5 dimensions, no study-specific routing
- Card sort screen (job seeker): 12 I/G/C cards, complete
- Study 3 files: complete 4-stage structure with competition element, card sort, and framing
- Bucket sort screen: 18 phrases from postings only, old bucket labels
- Assessment instructions, attention checks, open-ended screen: complete
- Lightcast data: mounted at `/Volumes/Expansion/All server/data/Burning Glass 2/merged_variables/`
- `phrases_candidate.csv`: does not exist

### What Was Missing

- Wage visibility as between-subjects manipulation in Study 2
- Study 2 4-stage structure (had 2 stages)
- Study 2 competition element (Study 3 had one; Study 2 did not)
- Study 2 transition screens
- Prewritten employer branding sections for Study 3 posting builder
- Expanded bucket sort (30-35 phrases with difficulty tiers)

---

## Sub-Agent 1 Outputs — Study 2 Structural Modifications

### Files Modified (7)

| File | Change |
|------|--------|
| `posting_A.md` | Added wage arm comment + `[WAGE_DISPLAY]` token in Stage 2 |
| `posting_B.md` | Added wage arm comment + `[WAGE_DISPLAY]` token in Stage 2 |
| `posting_C.md` | Added wage arm comment + `[WAGE_DISPLAY]` token in Stage 2 |
| `posting_D.md` | Added wage arm comment + `[WAGE_DISPLAY]` token in Stage 2 |
| `posting_E.md` | Added wage arm comment + `[WAGE_DISPLAY]` token in Stage 2 |
| `ranking_task_screens.md` | Added study-routing comment (Study 2: dims 1,3,5; Study 3: all 5); updated title and implementation notes |
| `study2_design_summary.md` | Full rewrite: 4-stage structure, wage visibility between-subjects, competition element, 3 ranking dimensions, updated predictions, timing, and output files |

### Files Created (2)

| File | Contents |
|------|----------|
| `study2_competition_screen.md` | Job seeker competition element (Stage 3): select 2 competitive postings, optionally revise card sort for those 2, with delta computation and theoretical purpose |
| `study2_transitions.md` | Three transition screens: Stage 1→2 (arm-specific wage reveal), Stage 2→3, Stage 3→4 |

### Key Design Decisions

- Stage 1 always shows "Salary: Undisclosed" (both arms) — consistent with Study 3
- Arm A wage reveal happens at Stage 1→2 transition (30-second minimum dwell)
- Arm B never sees wages; "Salary: Not disclosed" throughout Stages 2-4
- Competition element uses same 12 I/G/C cards as Stage 2 card sort, with "Keep my original selection" option
- Delta computation (Stage 3 - Stage 2 card profile) is the primary outcome for the competition stage

---

## Sub-Agent 2 Outputs — Prewritten Employer Branding Sections

### File Created (1)

| File | Contents |
|------|----------|
| `study3_prewritten_sections.md` | Five 1-2 sentence employer branding sections (purpose-social, purpose-innovation, good-employer, compensation, neutral/task), with source phrases, register notes, and alternate drafts |

### Lightcast Refinement

**Not performed.** The merged dataset (`full_dataset.parquet`, 226 columns) contains only structured variables — no raw posting text (`JobText`). Raw text is in per-month processed parquets on the Georgetown server and in XML archives on the external drive. All five sections are flagged as **DRAFT — PENDING LIGHTCAST REFINEMENT**.

### Phrases Flagged for Researcher Review

None flagged at this stage. `phrases_candidate.csv` does not exist, so Study 1 difficulty ratings could not be integrated. Future integration instructions are documented in the file.

---

## Sub-Agent 3 Outputs — Bucket Sort Screen

### File Modified (1)

| File | Change |
|------|--------|
| `bucket_sort_screen.md` | Expanded from 18 to 32 phrases; renamed buckets; added shared-use and draft comments; added composition summary and expanded scoring |

### Phrase Set Composition

| Category | Count | Requirement | Met? |
|----------|-------|-------------|------|
| Total phrases | 32 | 30-35 | Yes |
| Easy anchors | 8 (2 per bucket) | >= 8 | Yes |
| Medium phrases | 12 | >= 12 | Yes |
| Hard boundary cases | 12 | >= 10 | Yes |
| Hard: purpose/good_employer | 5 | >= 3 | Yes |
| Hard: purpose/task | 4 | >= 3 | Yes |
| Hard: good_employer/pecuniary | 3 | >= 3 | Yes |
| Company-specific names | 0 | 0 | Yes |

### Source

All phrases drawn from `refine_dictionaries.py` and assessment instructions examples. File marked **DRAFT — TO BE UPDATED AFTER STUDY 1** since `phrases_candidate.csv` does not exist.

---

## Consistency Checks

| Check | Result | Notes |
|-------|--------|-------|
| Wage display flags match design summary format | **PASS** | All 5 posting files use `[WAGE_DISPLAY]` token; design summary describes Arm A/B correctly |
| Prewritten section phrases consistent with bucket sort | **PASS** | No phrase used in a purpose section is rated as good_employer in bucket sort, and vice versa |
| Bucket sort phrase count in range | **PASS** | 32 phrases (within 30-35) |
| Shared use comment at top of bucket sort | **PASS** | Both `<!-- SHARED -->` and `<!-- DRAFT -->` comments present |
| All expected files exist | **PASS** | All 20 stimuli .md files confirmed |
| S5 source attribution | **FIXED** | "competitive salary" was attributed to Posting E (Thornbury), but Thornbury says "standard benefits package" — corrected to dictionary source |
| No stale bucket labels in other files | **PASS** | Grepped for old labels ("Mission and Values" etc.) — none found |

---

## Items Requiring Researcher Review Before IRB Submission

1. **Prewritten section register:** All five sections in `study3_prewritten_sections.md` are draft versions pending Lightcast refinement. Researcher should verify that the tone matches real job postings (especially purpose-social and purpose-innovation sections) before including in IRB materials.

2. **Bucket sort hard phrases:** 12 hard boundary cases have researcher-assigned expected buckets, but these are judgment calls. Researcher should review whether the expected bucket assignments for S21-S32 align with the theoretical framework (especially "we invest in our people" [S21] and "employee-first culture" [S22], both assigned to Organizational purpose per the assessment instructions' guidance that culture is purpose-adjacent).

3. **Study 2 competition element scarcity framing:** The prompt tells participants "for two of these five positions, several other strong candidates are already well into the hiring process" — researcher should verify that this framing is strong enough to activate scarcity perception without creating demand characteristics.

4. **Study 2 ranking dimension reduction:** Study 2 now uses 3 dimensions (perceived pay, values alignment, overall desirability) instead of 5. Researcher should confirm that dropping Dimensions 2 (Employer Investment) and 4 (Learning and Growth) does not compromise the theoretical structure. Study 3 retains all 5.

5. **Wage visibility arm labels:** Posting files use "Salary: Undisclosed" (Stage 1, both arms) vs. "Salary: Not disclosed" (Stage 2+, Arm B). Researcher should verify that this slight wording difference ("Undisclosed" vs. "Not disclosed") does not create a confound or tip off participants to the manipulation.

6. **Bucket sort timing:** With 32 phrases (up from 18), the bucket sort will take longer. The design summary estimates 4-5 minutes for Stage 4. Pilot testing should verify this does not push total session time beyond 30 minutes.

---

## Items Deferred Pending Study 1 Completion

1. **Bucket sort phrase replacement.** When `phrases_candidate.csv` exists with Study 1 classification data, replace dictionary-sourced phrases with empirically validated phrases. Prioritize phrases with `cross_firm_frequency > 3` and exclude `context_dependence = high`.

2. **Prewritten section anchor validation.** Cross-reference the source dictionary phrases in each prewritten section against Study 1 difficulty ratings. If any anchor phrase has low classification accuracy, revise the section wording.

3. **Hard phrase difficulty calibration.** Study 1 will produce empirical difficulty ratings for boundary phrases. Update the bucket sort difficulty assignments (easy/medium/hard) based on actual participant disagreement rates rather than researcher judgment.

4. **Lightcast register refinement.** When Georgetown server access is available, sample real postings by NAICS code and compare register against the prewritten sections. Update sections to match real employer language patterns.

5. **Bucket sort `DRAFT` flag removal.** Once the phrase set is updated with Study 1 data, remove the `<!-- DRAFT -->` comment from `bucket_sort_screen.md`.
