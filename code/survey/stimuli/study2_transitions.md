# Study 2 Transition Screens

Transition screens shown between stages. Each transition serves as a brief framing reset and, where applicable, introduces new information (wage reveal for Arm A).

---

## Transition 1: Stage 1 (Rankings) -> Stage 2 (Card Sort)

### Arm A — Wage Reveal Transition

> Thank you for your rankings.
>
> Before the next task, we can now share some additional information: salary ranges are available for each of these positions.
>
> Please take a moment to review the updated postings, including the salary information, before continuing.

*[Display all five postings with salary ranges visible. Enforce a minimum 30-second wait before the "Continue" button activates.]*

*[Record: `wage_reveal_view_time` — total time on this screen.]*

### Arm B — Simple Transition

> Thank you for your rankings.
>
> In the next task, you will look at each posting again and think about how you would present yourself as an applicant.

*[No salary information is revealed. Postings continue to show "Salary: Not disclosed."]*

*["Continue" button available immediately.]*

---

## Transition 2: Stage 2 (Card Sort) -> Stage 3 (Competition Element)

> One more scenario before we wrap up the main tasks.
>
> Imagine your job search has progressed — you have been actively applying and have a few processes underway.

*["Continue" button available immediately.]*

---

## Transition 3: Stage 3 (Competition Element) -> Stage 4 (Bucket Sort)

> Almost done. One final short task.
>
> In this last section, we will ask you to sort some phrases you may have noticed in the postings. This helps us understand how you processed the information.

*["Continue" button available immediately.]*

---

## Implementation Notes

- Each transition screen should be displayed as a standalone page with a centered "Continue" button.
- Transition 1 (Arm A) requires a minimum dwell time of 30 seconds to ensure participants actually review the wage information.
- All transition screens should record `screen_display_time` (time from display to "Continue" click).
- The arm assignment determines which version of Transition 1 is shown. Transitions 2 and 3 are identical across arms.
