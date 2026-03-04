# Study 3 Design Summary — Hiring Manager Job Posting Review Task

## Overview

Study 3 is the hiring manager parallel to Study 2. Where Study 2 examines how job seekers process employer signals in job postings, Study 3 examines what signals hiring managers reach for when trying to attract candidates — and how competitive pressure changes those choices. Both studies use the same five fictional job postings, the same four-stage skeleton, and the same between-subjects wage visibility manipulation (Arm A: wages shown; Arm B: wages hidden). Studies 2 and 3 share Stage 1 (rankings) and Stage 4 (bucket sort) identically, differing only in the Stage 1 framing: Study 3 participants rank postings "as you imagine a strong candidate would evaluate them" rather than from their own perspective. Stages 2 and 3 are new to Study 3, replacing Study 2's job seeker card sort with a hiring manager card sort and adding a competition manipulation.

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

## Stage Structure

| Stage | Task | Shared with Study 2? |
|-------|------|----------------------|
| 1 | Rankings (5 dimensions) | Yes — identical except framing |
| 2 | Hiring manager card sort (select 3 of 12 cards per posting) | No — new card pool |
| 3 | Competition element (yes/no change + single card per posting) | No — hiring manager version |
| 4 | Bucket sort | Yes — identical |

---

## Between-Subjects Factor

**Wage visibility:** Arm A (wages shown on all postings) vs Arm B (wages hidden; "Salary: Undisclosed").

Same randomization logic as Study 2. Wage visibility applies starting in Stage 2 (wages are always hidden in Stage 1). Assignment is at the participant level and persists through Stages 2, 3, and 4.

---

## Key Contrasts (Organized by Research Question)

### Q1 — Signal Detection: Do hiring managers perceive postings the same way job seekers do?

Stage 1 rankings are directly comparable across Study 2 and Study 3. Both groups rank the same postings on the same dimensions with the same instructions (Study 3 adds only the framing "as you imagine a strong candidate would evaluate them"). Differences in ranking patterns reveal whether hiring managers accurately model job seeker preferences or systematically over- or under-weight certain signal types.

Key comparison: Study 2 vs Study 3 rankings on perceived pay, values alignment, and overall desirability dimensions.

### Q2 — What do hiring managers reach for?

Stage 2 card type profiles (P-count, G-count, W-count, T-count per posting) reveal what signals hiring managers want to add to each posting. The key question is whether managers match their additions to the posting's existing signal type (reinforcement) or compensate by adding what the posting lacks (substitution).

Key comparison: P-type selection rate on purpose postings vs G-type selection rate on the good-employer posting vs W-type selection rate across all posting types.

### Q3 — Competition and wages: Do hiring managers reach for wages under competitive pressure?

Stage 3 W-type card selection rate by posting type. The field study finds that firms making purpose claims increase wages by approximately four percent more than firms not making purpose claims in tight labor markets. The prediction is that purpose posting managers reach for wages under competition more than good-employer posting managers — replicating the costly signaling mechanism from the supply side.

Key comparison: W-type card selection rate on purpose postings (A, B, D) vs good-employer posting (C) vs neutral posting (E) under competition.

### Q4 — Does wage visibility moderate what hiring managers add?

Does knowing the current wage (Arm A) change what hiring managers add under competition, relative to not knowing it (Arm B)? If purpose postings already show a high wage (Posting A, Arm A), managers may feel less pressure to add W-type cards. If the wage is hidden (Arm B), managers may reach for wages more because they cannot verify what is already offered.

Key comparison: Stage 3 W-type selection rate × Arm A vs Arm B, separately for high-wage purpose (A), low-wage purpose (B, D), high-wage good-employer (C), and neutral (E).

---

## Theoretical Mapping to Field Study

The field study identifies a complementarity between organizational purpose claims and wages in tight labor markets: firms that claim purpose and face competitive labor markets pay approximately four percent more than firms that do not claim purpose. This finding is consistent with costly signaling — purpose claims require wage backing to be credible, and firms signal their commitment by coupling purpose language with above-market compensation.

Study 3 tests the supply-side mechanism behind this finding. If hiring managers reviewing purpose-laden postings reach for W-type additions (wages, bonuses, compensation packages) under competitive pressure more than those reviewing good-employer or neutral postings, this supports the interpretation that firms recognize purpose claims need monetary backing. The card sort design also tests an alternative: if managers reach for more P-type additions (doubling down on purpose language), firms may believe purpose signals are self-reinforcing and do not require wage support.

The field study further finds heterogeneity by industry reputation (firms in high-polluting industries show larger purpose-wage complementarity) and by occupational age composition (younger-skewing occupations show stronger effects). Study 3's within-subject design across five postings allows testing whether managers respond differently to purpose postings that vary in wage level (A vs B/D) — a direct parallel to the heterogeneous effects observed in the field data.

---

## Timing Estimate

| Stage | Estimated Time |
|-------|---------------|
| Opening framing and reading | 3 min |
| Stage 1: Rankings (5 dimensions) | 5 min |
| Stage 2: Hiring manager card sort (5 postings × 3 cards) | 7–8 min |
| Stage 3: Competition element (5 postings × yes/no + card) | 4–5 min |
| Stage 4: Bucket sort | 5 min |
| **Total** | **24–26 min** |

If pilot testing exceeds 28 minutes, remove Dimension 4 (Learning and Growth) from Stage 1 first — it is the least theoretically essential and is shared with Study 2, which provides that data independently.

---

## Participant Population

Professionals with hiring or management experience. Recruited via Prolific with screener for current or recent managerial role (at least one year of experience evaluating candidates or making hiring decisions).

**Framing:** "Imagine you are a hiring manager at a mid-size firm. Your team is growing and you are looking to fill an analyst-level role."

---

## Output Files

| File | Contents |
|------|----------|
| `posting_A.md` – `posting_E.md` | Full text of each posting (shared with Study 2) |
| `ranking_task_screens.md` | Five ranking dimension screens (shared with Study 2) |
| `study3_framing_screen.md` | Opening framing and transition screens |
| `study3_structure.md` | Four-stage structure documentation |
| `study3_card_sort_screen.md` | Hiring manager card sort instructions and card pool |
| `study3_competition_screen.md` | Competition element instructions and recording logic |
| `bucket_sort_screen.md` | Bucket sort task (shared with Study 2) |
| `study3_design_summary.md` | This file |
