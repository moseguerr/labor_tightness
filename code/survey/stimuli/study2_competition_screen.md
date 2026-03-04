# Competition Element — Study 2, Stage 3

Presented after the job seeker card sort (Stage 2). This stage introduces competitive scarcity for two of the five postings and tests whether job seekers adjust their self-presentation strategy under perceived competition. Wage visibility continues per arm assignment from Stage 2.

---

## Screen Text

> You have been actively applying and have a few processes underway. You just found out that for two of these five positions, several other strong candidates are already well into the hiring process.
>
> Which two positions do you think are most likely to be the competitive ones?

*[Display all five posting titles as selectable options. Participant selects exactly two.]*

| Posting | Title Displayed |
|---------|-----------------|
| A | Vantage Strategy Group — Strategy Analyst |
| B | Bridgewell Financial — Financial Analyst |
| C | Crestline Industries — Marketing Coordinator |
| D | Novalink Group — People Analytics Analyst |
| E | Thornbury Corp — Operations Analyst |

---

## Follow-Up: Revised Card Sort (per selected posting)

For each of the two postings selected as competitive, display the following screen:

> You selected **[FIRM NAME] — [ROLE TITLE]** as one of the competitive positions. Knowing that several strong candidates are already in the process, would you change anything about how you presented yourself?
>
> Select your revised top 3 statements — or click "Keep my original selection."

*[Display the full posting text. Arm A: salary visible. Arm B: "Salary: Not disclosed."]*

*[Display the same 12-card pool from Study 2 Stage 2 (see card_sort_screen.md). Participant selects exactly 3 cards OR clicks "Keep my original selection."]*

### Card Pool (same 12 cards as Stage 2)

**Identity Cards (I) — responding to purpose signals**

| ID | Card Text |
|----|-----------|
| I1 | My passion for this organization's mission and what it is working to achieve |
| I2 | My alignment with this company's values and the kind of work they stand for |
| I3 | My belief in what this organization is building and my desire to be part of it |
| I4 | My fit with how this team thinks and operates |

**Good-Employer Responsiveness Cards (G) — responding to employer investment signals**

| ID | Card Text |
|----|-----------|
| G1 | My long-term commitment to growing within an organization that invests in its people |
| G2 | My appreciation for environments that support professional development and work-life balance |
| G3 | My interest in the specific development opportunities and resources this firm offers |

**Competence Cards (C) — pure productivity signal, employer-type-neutral**

| ID | Card Text |
|----|-----------|
| C1 | My technical skills and analytical background relevant to this role |
| C2 | My track record of delivering results in similar positions |
| C3 | My academic achievements and relevant coursework |
| C4 | My leadership experience and ability to work across functions |
| C5 | My ability to contribute immediately given my prior experience |

---

## Posting Order

Present the two follow-up card sorts in the order the participant selected them. Each posting is displayed on its own screen.

---

## Recording Instructions (for survey programmer)

### Scarcity Perception (initial selection)

- `competitive_posting_1`: which posting was selected first (A–E)
- `competitive_posting_2`: which posting was selected second (A–E)
- `scarcity_response_time`: time from screen display to confirmation of the two selections

### Revised Card Sort (per selected posting)

Per posting, record:
- `keep_original`: boolean — did the participant click "Keep my original selection"?
- `revised_cards`: if not keep_original, which 3 cards were selected (card IDs)
- `revised_card_order`: the order in which the 3 cards were selected
- `response_time`: time from screen display to submission

### Computed Variables

- `delta_identity_count`: (number of I-type cards in Stage 3 selection) minus (number of I-type cards in Stage 2 selection for the same posting)
- `delta_good_employer_count`: (number of G-type cards in Stage 3 selection) minus (number of G-type cards in Stage 2 selection for the same posting)
- `delta_competence_count`: (number of C-type cards in Stage 3 selection) minus (number of C-type cards in Stage 2 selection for the same posting)
- If `keep_original` is true, all deltas are 0 for that posting.
- Compute deltas separately for each of the two selected postings.
- `any_change`: boolean — did the participant revise at least one of the two postings?
- `change_direction_summary`: across both postings, net shift in card type counts (e.g., +1 C, -1 I)

Card labels (I1, G1, C1, etc.) are NOT shown to participants.

---

## Implementation Notes

- Enforce exactly two selections in the initial scarcity question before advancing.
- For each follow-up screen, the participant must either select exactly 3 cards OR click "Keep my original selection" — not both.
- Randomize card display order independently for each posting.
- The "Keep my original selection" button should be visually distinct from the card pool (e.g., below the card grid, styled as a secondary action).
- The full posting text (with wage arm applied) should remain visible while the participant makes their selections.
- Display the participant's original Stage 2 card selection for reference (e.g., "Your original selection: [card texts]" shown above or beside the card pool).

---

## Theoretical Purpose

This stage tests whether competitive pressure changes which signals job seekers choose to emphasize in their self-presentation — and, critically, whether the direction of that shift depends on the type of employer signal in the posting.

The core question is: when a job seeker learns that competition for a position is intense, do they shift toward competence-based self-presentation (the safe default that signals productivity regardless of employer type), or do they double down on identity matching (signaling deeper alignment with the employer's stated purpose or values)?

**Predictions:**

1. **Competence shift as default:** Under competition, most participants will shift toward C-type cards across all postings, reflecting a "prove yourself" instinct when stakes are higher.

2. **Signal-contingent identity persistence:** For purpose postings (A, B, D) backed by high wages (Posting A in Arm A), participants may maintain or increase I-type card selection — the reasoning being that identity matching is a stronger differentiator for purpose-driven employers, and competition makes differentiation more valuable.

3. **Purpose + low wage = competence retreat:** For purpose postings with low wages (B, D), competition should amplify the shift toward C-type cards. The low wage already undermined the credibility of the purpose signal (observed in Stage 2); competition adds urgency, making the safe competence strategy even more attractive.

4. **Good-employer posting (C):** Participants may shift toward G-type cards under competition — mirroring the employer's investment language to signal "I am worth investing in" — or toward C-type if they view competition as requiring proof of productivity.

5. **Scarcity perception measure:** Which two postings participants select as "most likely to be competitive" reveals their mental model of labor market tightness. If participants disproportionately select high-wage postings (A, C) as competitive, this suggests they associate higher compensation with stronger candidate pools — consistent with the field study's finding that wages and competition co-occur.

**Connection to field study:** The field study finds that firms making purpose claims in tight markets pay ~4% higher wages. Study 2 Stage 3 tests the demand-side mechanism: do job seekers facing competition treat purpose signals differently depending on wage backing? If purpose + high wage postings elicit sustained identity matching under competition while purpose + low wage postings trigger competence retreat, this supports the interpretation that wage backing is necessary for purpose signals to function as credible attraction devices even from the job seeker's perspective.
