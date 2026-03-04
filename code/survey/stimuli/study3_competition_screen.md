# Competition Element — Study 3, Stage 3

Presented after the hiring manager card sort (Stage 2). This is the core experimental manipulation for Study 3. Wage visibility continues per arm assignment from Stage 2.

---

## Screen Text

> HR has just flagged that several strong candidates for these types of roles are already well into hiring processes at other firms. You have some flexibility to strengthen your postings.
>
> For each of the five postings, would you make a change given this competition? And if so, what is the single most important thing you would add or strengthen?

---

## Per-Posting Display

For each posting, display in sequence:

**[FIRM NAME] — [ROLE TITLE]**

*[Display the full posting text. Arm A: salary visible. Arm B: "Salary: Undisclosed."]*

> Would you make a change to this posting?

- [ ] Yes
- [ ] No

*[If "Yes" is selected, display the 12-card pool below. Participant selects ONE card only.]*

> What is the single most important addition?

### Card Pool (same 12 cards as Stage 2)

**Purpose Cards (P)**

| ID | Card Text |
|----|-----------|
| P1 | Strengthen the description of our mission and what we stand for |
| P2 | Add language about the impact this role has on our broader goals |
| P3 | Describe the kind of people and values that thrive here |
| P4 | Clarify what makes our organization distinct from competitors |

**Good-Employer Cards (G)**

| ID | Card Text |
|----|-----------|
| G1 | Add details about career development and learning opportunities |
| G2 | Highlight flexibility, hybrid arrangements, or work-life balance |
| G3 | Mention mentorship, team support, or internal mobility |

**Wage and Compensation Cards (W)**

| ID | Card Text |
|----|-----------|
| W1 | Add or increase the stated salary range |
| W2 | Mention performance bonuses or equity opportunities |
| W3 | Highlight the overall compensation and benefits package |

**Task and Role Cards (T)**

| ID | Card Text |
|----|-----------|
| T1 | Make the role description more specific and concrete |
| T2 | Clarify what success looks like in this role in the first year |

---

## Posting Order

Present all five postings in the same randomized order used throughout the session. Each posting is displayed on its own screen with the yes/no question and (conditionally) the card pool.

---

## Recording Instructions (for survey programmer)

Per posting, record:
- `changed`: yes / no
- `card_selected`: if yes, which card was selected (single card ID)
- `card_type`: if yes, the type of the selected card (P / G / W / T)
- `response_time`: time from screen display to submission

Compute and store:
- `change_rate`: proportion of postings (out of 5) where participant chose to change
- `card_type_distribution`: across all changes made, what proportion were P / G / W / T type
- `by_posting_type`: break down card selections by the signal type of the posting being changed:
  - Purpose-innovation postings (A, D): card type distribution
  - Purpose-social posting (B): card type distribution
  - Good-employer posting (C): card type distribution
  - Neutral posting (E): card type distribution

Card labels (P1, G1, W1, T1, etc.) are NOT shown to participants.

---

## Implementation Notes

- Enforce that the participant selects either "Yes" or "No" before advancing.
- If "Yes" is selected, enforce exactly 1 card selection before advancing.
- If "No" is selected, do not display the card pool — advance directly to the next posting.
- All 12 cards should be visually identical in size, font, and prominence.
- The full posting text should remain visible while the participant makes their selection.

---

## Theoretical Purpose

This is the experimental test of the field study mechanism.

The field study finds that in tight labor markets, firms making purpose claims increase wages by approximately four percent more than firms not making purpose claims. The interpretation is costly signaling: purpose claims need wage backing to be credible under competition.

Study 3 Stage 3 tests this from the hiring manager side: when told there is competition for candidates, do hiring managers managing purpose postings reach for W-type cards (wages, compensation) more than hiring managers managing good-employer or neutral postings?

Key comparisons:
- W-type card selection rate on purpose postings (A, B, D) vs good-employer posting (C) vs neutral posting (E) under competition
- W-type card selection rate by wage visibility arm: do managers who can see the current wage (Arm A) differ from those who cannot (Arm B)?
- Change rate by posting type: are managers more likely to change purpose postings or good-employer postings under competition?
- Within purpose postings: do social-purpose postings (B, low wage) elicit more W-type selections than innovation-purpose postings (A, high wage; D, low wage)?
