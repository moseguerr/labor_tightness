<!-- SHARED: used identically in Study 2 Stage 4 and Study 3 Stage 4
     Any changes to this file apply to both studies -->
<!-- DRAFT — TO BE UPDATED AFTER STUDY 1 when phrases_candidate.csv exists -->

# Bucket Sort Screen — Shared: Study 2 (Stage 4) and Study 3 (Stage 4)

This task is identical across Study 2 and Study 3. It serves as a manipulation check and a direct measure of signal detection — whether participants can reliably distinguish organizational purpose, good-employer, compensation, and task signal types in job posting language.

---

## Instruction Text

> "Below are phrases that employers sometimes use in job postings. Drag each phrase into the bucket that best describes what it is communicating to a job seeker. Use the Not Sure bucket if you are genuinely uncertain — there is no penalty for using it."

---

## Buckets (Categories)

| Bucket | Label Shown to Participant | Description (shown on hover or in a help tooltip) |
|--------|---------------------------|---------------------------------------------------|
| 1 | **Organizational purpose** | The organization is describing who it is, what it stands for, or what it is trying to achieve in the world |
| 2 | **Good employer** | The organization is describing how it treats, develops, or invests in its employees — working conditions, career growth, and non-monetary benefits |
| 3 | **Compensation & benefits** | The organization is signaling something about salary, bonuses, financial rewards, or insurance/retirement benefits |
| 4 | **Job tasks** | The phrase describes what the person in this role would actually do day-to-day |
| 5 | **Not sure** | The phrase does not clearly fit any of the categories above, or you are genuinely uncertain |

---

## Phrase Pool

Phrases are drawn from the five fictional postings and from the research dictionary. The pool includes a mix of purpose, good-employer, compensation, task, and boundary phrases to test classification accuracy. Phrases are presented in randomized order.

### Easy Anchors (8 phrases)

These serve as attention checks and reliability baseline. Virtually all participants should classify them correctly.

| ID | Phrase | Source | Expected Bucket | Difficulty | Boundary Pair |
|----|--------|--------|-----------------|------------|---------------|
| S1 | "mission driven" | dictionary: meaningful_work / societal values | Organizational purpose | Easy | none |
| S2 | "make a real difference" | dictionary: meaningful_work / impact | Organizational purpose | Easy | none |
| S3 | "mentorship program" | dictionary: career_development / mentorship | Good employer | Easy | none |
| S4 | "flexible work schedule" | dictionary: job_design / flexible work | Good employer | Easy | none |
| S5 | "competitive salary" | dictionary: pecuniary / additional | Compensation & benefits | Easy | none |
| S6 | "401k match" | dictionary: pecuniary / retirement | Compensation & benefits | Easy | none |
| S7 | "manage cross-functional teams" | dictionary: job_tasks | Job tasks | Easy | none |
| S8 | "analyze customer data" | dictionary: job_tasks / skills | Job tasks | Easy | none |

### Medium Phrases (12 phrases)

Most participants agree after brief reflection. The category is inferable but takes a moment. Includes boundary pairs and non-obvious single-category items.

| ID | Phrase | Source | Expected Bucket | Difficulty | Boundary Pair |
|----|--------|--------|-----------------|------------|---------------|
| S9 | "innovative work environment" | dictionary: meaningful_work / innovation | Organizational purpose | Medium | purpose/good_employer |
| S10 | "creative environment" | dictionary: meaningful_work / innovation | Organizational purpose | Medium | purpose/good_employer |
| S11 | "vibrant work environment" | dictionary: meaningful_work / innovation | Organizational purpose | Medium | purpose/good_employer |
| S12 | "making an impact" | dictionary: meaningful_work / societal values | Organizational purpose | Medium | purpose/task |
| S13 | "challenging and rewarding" | dictionary: meaningful_work / impact | Organizational purpose | Medium | purpose/task |
| S14 | "positive impact" | dictionary: meaningful_work / impact | Organizational purpose | Medium | purpose/task |
| S15 | "comprehensive benefits package" | dictionary: pecuniary / additional | Compensation & benefits | Medium | good_employer/pecuniary |
| S16 | "education assistance" | dictionary: pecuniary / tuition | Compensation & benefits | Medium | good_employer/pecuniary |
| S17 | "employee discount" | dictionary: pecuniary / additional | Compensation & benefits | Medium | good_employer/pecuniary |
| S18 | "shared values" | dictionary: meaningful_work / societal values | Organizational purpose | Medium | none |
| S19 | "advancement opportunities" | dictionary: career_development / progression | Good employer | Medium | none |
| S20 | "work-life balance" | dictionary: job_design / work-life balance | Good employer | Medium | none |

### Hard Boundary Cases (12 phrases)

Thoughtful participants genuinely disagree. Both categorizations are theoretically defensible. The ambiguity is theoretically motivated — it connects to why purpose and good-employer signals have different wage implications.

| ID | Phrase | Source | Expected Bucket | Difficulty | Boundary Pair |
|----|--------|--------|-----------------|------------|---------------|
| S21 | "we invest in our people" | assessment instructions example | Organizational purpose | Hard | purpose/good_employer |
| S22 | "employee-first culture" | assessment instructions example | Organizational purpose | Hard | purpose/good_employer |
| S23 | "people are our greatest asset" | dictionary: organizational_culture / collaborative | Organizational purpose | Hard | purpose/good_employer |
| S24 | "great place to work" | dictionary: organizational_culture / workplace recognition | Organizational purpose | Hard | purpose/good_employer |
| S25 | "solving global challenges" | dictionary: meaningful_work / global challenges | Organizational purpose | Hard | purpose/task |
| S26 | "creative problem solving" | dictionary: meaningful_work / innovation | Organizational purpose | Hard | purpose/task |
| S27 | "driving progress" | dictionary: meaningful_work / innovation | Organizational purpose | Hard | purpose/task |
| S28 | "total rewards" | compensation industry term | Compensation & benefits | Hard | good_employer/pecuniary |
| S29 | "employee wellness programs" | dictionary: job_design / work-life balance + pecuniary / additional | Good employer | Hard | good_employer/pecuniary |
| S30 | "wellness benefits" | dictionary: pecuniary / additional | Compensation & benefits | Hard | good_employer/pecuniary |
| S31 | "reinvest in our employees" | dictionary: organizational_culture / recognition | Organizational purpose | Hard | purpose/good_employer |
| S32 | "building resilient societies" | dictionary: meaningful_work / global challenges | Organizational purpose | Hard | purpose/task |

---

## Composition Summary

| Category | Count | Requirement | Met? |
|----------|-------|-------------|------|
| Total phrases | 32 | 30-35 | Yes |
| Easy anchors | 8 | >= 8 (2 per category) | Yes |
| Medium phrases | 12 | >= 12 | Yes |
| Hard boundary cases | 12 | >= 10 | Yes |
| Hard: purpose/good_employer | 5 (S21-S24, S31) | >= 3 | Yes |
| Hard: purpose/task | 4 (S25-S27, S32) | >= 3 | Yes |
| Hard: good_employer/pecuniary | 3 (S28-S30) | >= 3 | Yes |
| Company-specific names | 0 | 0 | Yes |
| Phrase length (words) | 2-5 | 2-6 | Yes |

---

## Implementation Notes

- Display all buckets as labeled drop zones at the top of the screen.
- Display all phrases as draggable cards below the buckets.
- Randomize phrase order independently for each participant.
- Allow participants to reassign phrases by dragging them between buckets.
- Enforce that all phrases are sorted before the participant can advance.
- Record the bucket assignment for each phrase and the total time to complete the task.
- "Not sure" is a legitimate category — do not discourage its use.

Randomize phrase order across participants.
Record bucket assignment and time on each phrase.
Flag responses under 2 seconds as potentially rushed.

---

## Scoring (for researcher use only — not shown to participants)

- **Correct classification:** phrase sorted into the matching expected bucket.
- **Boundary error:** phrase sorted into an adjacent or theoretically defensible category (e.g., a culture phrase sorted into Good employer, or a purpose phrase sorted into Job tasks when the phrase sits on the purpose/task boundary).
- **Misclassification:** phrase sorted into an unrelated category.

Compute per participant:
- `accuracy`: proportion of phrases correctly classified
- `purpose_accuracy`: accuracy on Organizational purpose phrases only
- `good_employer_accuracy`: accuracy on Good employer phrases only
- `compensation_accuracy`: accuracy on Compensation & benefits phrases only
- `task_accuracy`: accuracy on Job tasks phrases only
- `boundary_error_rate`: proportion classified into adjacent categories
- `hard_agreement`: proportion of hard phrases matching expected bucket (measure of construct clarity)
- `easy_accuracy`: proportion of easy phrases correctly classified (attention check proxy)
