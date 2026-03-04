# Study 2 Design Summary — Job Seeker Ranking, Application, and Competition Task

## Overview

Study 2 uses a mock job board to examine how job seekers process three types of non-wage employer signals — organizational purpose (innovation), organizational purpose (social), and good-employer — and how wage information and competitive pressure update perceptions and self-presentation strategy. Participants see five fictional postings, rank them on three dimensions with wages hidden, complete a card sort application task (with wages revealed for Arm A), face a competition scenario for two self-selected postings, and finish with a bucket sort manipulation check.

**Between-subjects factor:** Wage visibility (Arm A: wages shown from Stage 2 onward; Arm B: wages never shown, "Salary: Not disclosed" throughout).

---

## Design Matrix

| Posting | Firm | Occupation | Language Type | Wage Level | Salary Range |
|---------|------|------------|---------------|------------|--------------|
| A | Vantage Strategy Group | Strategy Analyst | Purpose — innovation | High | $95,000 – $110,000 |
| B | Bridgewell Financial | Financial Analyst | Purpose — social | Low | $52,000 – $62,000 |
| C | Crestline Industries | Marketing Coordinator | Good-employer | High | $72,000 – $85,000 |
| D | Novalink Group | People Analytics Analyst | Purpose — innovation | Low | $58,000 – $68,000 |
| E | Thornbury Corp | Operations Analyst | Neutral (baseline) | Medium | $68,000 – $78,000 |

---

## Between-Subjects Factor: Wage Visibility

| Arm | Stage 1 | Stages 2–4 |
|-----|---------|------------|
| Arm A (wages visible) | "Salary: Undisclosed" | Actual salary range shown |
| Arm B (wages hidden) | "Salary: Undisclosed" | "Salary: Not disclosed" |

Randomization is at the participant level — all five postings display the same arm for a given participant. Assignment is determined at session start and persists through all stages.

---

## Stage Structure

| Stage | Task | Description |
|-------|------|-------------|
| 1 | Rankings (3 dimensions) | Rank all five postings on perceived pay, values alignment, and overall desirability. Wages hidden for both arms. |
| 2 | Card Sort | Select 3 of 12 cover-letter statements per posting. Arm A: wages revealed. Arm B: wages remain hidden. |
| 3 | Competition Element | Select which two postings are most competitive, then optionally revise card selections for those two postings. |
| 4 | Bucket Sort | Sort phrases from postings into labeled categories (manipulation check). |

Transitions between stages are specified in `study2_transitions.md`.

---

## Key Contrasts

| Contrast | Postings | What It Tests |
|----------|----------|---------------|
| Wage credibility within purpose (innovation) | A vs D | Same language type, high vs low wage. Does wage update perceptions of a purpose-claiming employer? |
| Purpose vs good-employer at equal high wage | A vs C | Does signal type affect attraction when wages are equal? Identity appeal vs concrete investment. |
| Social purpose + low wage vs good-employer + high wage | B vs C | Does an honest good-employer signal outperform an unsubstantiated purpose claim? |
| Social purpose + low wage vs neutral baseline | B vs E | Does purpose language without wage backing even beat no signal? |
| Innovation purpose + low wage vs neutral baseline | D vs E | Same question for innovation-framed purpose. |
| Signal effect relative to no signal | Any vs E | Posting E enables estimating the pure effect of each signal type. |
| Arm A vs Arm B (within-stage) | All | Does wage visibility change card sort profiles (Stage 2), scarcity perceptions (Stage 3), or competition-induced shifts (Stage 3)? |

---

## Measures

### Stage 1 — Ranking Task (Wages Hidden)

Three forced-rank dimensions, each across all five postings:

1. **Perceived pay** — which employer pays more? Tests wage inference from signal type alone.
2. **Values alignment** — whose values match yours? Tests signal detection for purpose language.
3. **Overall desirability** — where would you most want to work? Primary attraction outcome.

Note: Dimensions 2 (Employer Investment) and 4 (Learning and Growth) are used in Study 3 only. See `ranking_task_screens.md` for the full five-dimension set and the study-routing note.

**Open-ended item:** "What stood out most about each posting?" (100 characters per posting, qualitative signal detection)

### Stage 2 — Card Sort Application Task

For each posting, select 3 of 12 cover-letter statements to emphasize. Cards fall into three types:

- **Identity cards (I1–I4):** respond to purpose signals (mission, values, building something, team fit)
- **Good-employer responsiveness cards (G1–G3):** respond to investment signals (commitment, development, opportunities)
- **Competence cards (C1–C5):** pure productivity signals (skills, track record, academic, leadership, immediate contribution)

Arm A participants see salary ranges on postings. Arm B participants see "Salary: Not disclosed."

### Stage 3 — Competition Element

Participant selects which two of the five postings are most likely to be competitive (scarcity perception measure). For each of those two postings, they either revise their top-3 card selection or click "Keep my original selection." See `study2_competition_screen.md` for full instructions.

Key recorded variables:
- Which two postings were identified as competitive
- Revised card selections (or keep_original flag)
- Card-type deltas: Stage 3 minus Stage 2 card profile at I/G/C level

### Stage 4 — Bucket Sort

Sort phrases extracted from postings into labeled categories. Shared with Study 3. See `bucket_sort_screen.md`.

### Attention Checks

1. (After rankings) Which posting mentioned a mentorship program and learning budget? -> Crestline Industries
2. (After card sort) Which phrase appeared in a posting? -> "reducing inequality" (from Bridgewell Financial)

---

## Predictions

### Stage 1 Rankings (Wages Hidden)

| Dimension | Predicted Rank Order (1=highest) | Rationale |
|-----------|----------------------------------|-----------|
| Perceived pay | A > E > C > D > B | Purpose-innovation signals ambition; neutral baseline anchors middle; social purpose may signal lower pay |
| Values alignment | B > A ≈ D > C > E | Purpose postings (both types) should dominate; good-employer and neutral should lag |
| Overall desirability | A > C > D ≈ E > B | High-wage purpose and good-employer should lead; low-wage purpose may trail neutral |

### Stage 2 Card Sort

| Posting | Predicted Card Profile (Arm A) | Key Prediction |
|---------|-------------------------------|----------------|
| A (Purpose-Innovation + High) | Majority I-type | Wage backs the purpose signal -> identity matching activated |
| B (Purpose-Social + Low) | Shift from I-type toward C-type | Low wage undermines purpose credibility -> competence-default |
| C (Good-Employer + High) | Majority G-type | Explicit investment language -> participants mirror the signal |
| D (Purpose-Innovation + Low) | Shift from I-type toward C-type | Same wage-undermining effect as B |
| E (Neutral + Medium) | Majority C-type | No signal to respond to -> competence as default strategy |

**Between-arm comparison (Stage 2):** Arm B participants (no wage information) should show less differentiation in card profiles across postings — without wage data to confirm or undermine signals, the wage-credibility mechanism is attenuated.

### Stage 3 Competition Element

**Scarcity perception:** Participants are expected to disproportionately select high-wage postings (A, C) as competitive, reflecting the intuition that better-paying roles attract stronger candidate pools.

**Card sort shifts under competition:**
- Default prediction: shift toward C-type cards (competence as safe strategy under pressure)
- Purpose + high wage (A, Arm A): participants may maintain I-type cards — identity matching is a stronger differentiator and the high wage validates the signal
- Purpose + low wage (B, D): competition amplifies the shift toward C-type — low wage already undermined purpose credibility, competition adds urgency
- Good-employer (C): possible shift toward G-type ("I am worth investing in") or toward C-type (proving productivity)

**Between-arm comparison (Stage 3):** Arm A participants who can see that Posting A pays well may feel less pressure to shift toward C-type under competition, while Arm B participants (no wage info) should show a more uniform competence shift across all postings.

---

## Theoretical Mapping to Field Study

| Study 2 Finding | Field Study Connection |
|-----------------|----------------------|
| Purpose + high wage ranks highest on overall desirability | Firms making purpose claims in tight markets offer ~4% higher wages — consistent with costly signaling |
| Purpose + low wage falls below neutral on desirability | Without wage backing, purpose claims lose attraction power — the signal is not credible |
| Card sort shifts from identity to competence on low-wage purpose postings | Job seekers detect the mismatch and adjust self-presentation away from identity matching |
| Good-employer + high wage competes with purpose + high wage | Good-employer signals are a viable alternative attraction mechanism that does not require identity alignment |
| Perceived pay rankings before wages are revealed | Tests whether purpose language alone inflates or deflates wage expectations |
| Competition-induced competence shift is moderated by wage backing | Under competitive pressure, purpose + high wage sustains identity matching while purpose + low wage triggers competence retreat — paralleling the field finding that purpose claims need wage backing under tightness |
| Arm A vs Arm B differences in competition response | Tests whether the wage-credibility mechanism operates through information (knowing the wage) rather than inference (guessing from signals) |

---

## Wage Calibration

Salary ranges calibrated against BLS OES data (local parquet: `data/OESM/2021.parquet`, inflated to 2024).

| Posting | SOC | SOC Title | BLS Mean 2021 | Est. Mean 2024 | Target Percentile | Range Used |
|---------|-----|-----------|---------------|-----------------|--------------------|----|
| A | 13-1111 | Management Analysts | $100,530 | $108,572 | ~75th (early-career metro) | $95,000 – $110,000 |
| B | 13-2054 | Financial and Investment Analysts | $103,020 | $111,262 | ~25th (early-career metro) | $52,000 – $62,000 |
| C | 13-1161 | Market Research Analysts | $76,080 | $82,166 | ~75th (early-career metro) | $72,000 – $85,000 |
| D | 13-1141 | Compensation/Benefits/Job Analysis | $73,810 | $79,715 | ~25th (early-career metro) | $58,000 – $68,000 |
| E | 15-2031 | Operations Research Analysts | $95,830 | $103,496 | ~50th (early-career metro) | $68,000 – $78,000 |

National means are for all experience levels. Early-career (2-3 years) in a major metro area is approximately p25–p50 of the national all-experience distribution, depending on occupation. The ranges above reflect this adjustment.

---

## Participant Population

University students with a business background (undergraduate or MBA). Recruited via Georgetown behavioral lab or Prolific with screener for current business student or recent business graduate.

**Framing:** "Imagine you are a recent business school graduate, approximately two to three years into your career, actively looking for your next role."

---

## Session Timing

Target: 24–30 minutes total.

| Segment | Estimated Time |
|---------|---------------|
| Instructions and framing | 2 min |
| Reading five postings | 5–6 min |
| Stage 1: Three ranking tasks | 4–5 min |
| Open-ended post-ranking | 2 min |
| Transition (wage reveal for Arm A) | 1 min |
| Stage 2: Five card sorts | 7–8 min |
| Transition to competition | 0.5 min |
| Stage 3: Competition element (2 postings) | 3–4 min |
| Transition to bucket sort | 0.5 min |
| Stage 4: Bucket sort | 4–5 min |
| Attention checks and debrief | 2 min |

If pilot testing exceeds 30 minutes, consider reducing the open-ended item (Stage 1) to a single "most notable" posting rather than all five.

---

## Output Files

| File | Contents |
|------|----------|
| `posting_A.md` – `posting_E.md` | Full text of each posting (Stage 1 and Stage 2 versions, with wage arm flag) |
| `ranking_task_screens.md` | Ranking dimension screens with instructions (Study 2: Dims 1, 3, 5) |
| `open_ended_screen.md` | Post-ranking qualitative item |
| `card_sort_screen.md` | Card sort instructions and full card pool |
| `study2_competition_screen.md` | Competition element instructions, card pool, and recording logic |
| `study2_transitions.md` | Transition screens between stages (arm-specific) |
| `bucket_sort_screen.md` | Bucket sort task (shared with Study 3) |
| `attention_check_items.md` | Both attention checks with correct answers |
| `study2_design_summary.md` | This file |
