# Assessment Instructions: Study 1 Phrase Classification Stimuli

You are helping select stimuli for a behavioral experiment that tests whether people can distinguish two types of non-wage language employers use in job postings. Your task is to assess each phrase as a potential experimental stimulus.

---

## THE THREE SIGNAL TYPES

**ORGANIZATIONAL PURPOSE** signals who the organization is and what it stands for. It invites identity-based sorting. The job seeker asks: does this mission align with my values -- is this an organization I want to be part of?

Purpose is not limited to prosocial or humanitarian missions. A firm's purpose can be to build the most technically excellent product in the space, to be at the frontier of an industry, to reshape how a field operates, or to be part of a team that is genuinely the best at what it does. What makes something a purpose claim is that it connects to a job seeker's identity -- something they could say "that is who I am and what I care about."

Culture is purpose-adjacent, not good-employer. "Collaborative culture" or "fast-paced innovative culture" signals shared ways of being inside the organization -- it is an identity claim, not a perk.

Examples: "mission-driven", "make a real difference", "work with purpose", "shared values", "collaborative culture", "be part of something bigger", "redefining what's possible in our industry", "join the team building the future of analytics"

**GOOD-EMPLOYER** signals how the organization will treat you as an employee. These are non-pecuniary but transactional -- concrete, legible employment conditions and perks that do not require identity alignment. The job seeker asks: will I be treated well here? Will I get things I value beyond salary?

Good-employer signals are about benefits and working conditions, not about organizational identity. They can in principle substitute for wages: an employer can attract workers by offering strong development programs or flexibility instead of higher pay.

Examples: "career development programs", "work-life balance", "flexible schedule", "remote work options", "comprehensive benefits package", "tuition reimbursement", "job security", "learning and development resources", "mentorship program"

**PECUNIARY BENEFITS** are direct monetary signals. They are transactional and wage-adjacent.

Examples: "competitive salary", "performance bonus", "401k match", "equity package", "profit sharing", "annual merit increase"

**JOB TASKS** describe what the role involves day-to-day, not what the organization offers.

Examples: "manage a cross-functional team", "develop financial models", "analyze customer data"

**UNCLEAR / BOILERPLATE** are phrases that cannot be reliably assigned to any category, are too generic to be useful as stimuli, or are pure corporate filler.

---

## THE KEY BOUNDARY: PURPOSE vs GOOD-EMPLOYER

This is the most theoretically important boundary. These two signal types have opposite implications for wages:

- Good-employer signals can substitute for wages. A firm can offer strong development programs or flexibility instead of higher pay, and workers may accept the trade-off.
- Purpose claims need wage backing to be credible. A firm that claims social or organizational purpose without paying competitively appears instrumental -- the purpose claim looks like a cost-cutting tactic rather than genuine identity alignment.

A phrase sits on this boundary when:
- It could be read as "here is who we are and what we stand for" (purpose -- identity-based) AND
- It could be read as "here is what we offer you as an employee" (good-employer -- transactional)

Examples of genuinely hard boundary cases:
- "we invest in our people" -- statement of organizational values (purpose) or promise about employment conditions (good-employer)?
- "employee-first culture" -- shared organizational identity (purpose) or signal about how they treat staff (good-employer)?
- "people are our greatest asset" -- organizational purpose claim or HR branding language?

**Culture cues are purpose-adjacent.** If the phrase signals a shared way of being, thinking, or working together, classify as purpose even if it sounds like a working condition.

---

## DIFFICULTY CALIBRATION

**EASY**: Virtually all participants would agree immediately. The phrase unambiguously belongs to one category. Use for attention checks.

**MEDIUM**: Most participants agree after brief reflection. The category is inferable but takes a moment.

**HARD**: Thoughtful participants genuinely disagree. Both categorizations are theoretically defensible. The ambiguity must be theoretically motivated -- it must connect to why purpose and good-employer signals have different wage implications. Surface vagueness alone ("this could mean different things") is not sufficient for HARD.

**Default to HARD when uncertain.** Hard boundary cases are the scientific contribution of Study 1, not a problem to avoid.

A rationale for HARD must reference the theoretical mechanism. Bad rationale: "this phrase is vague." Good rationale: "this phrase could function as an identity-based sorting signal (applicant asks whether this matches their values) or as an employment-condition signal (applicant asks whether the firm will invest in them) -- both are theoretically defensible and the two have opposite predicted wage relationships."

---

## OUTPUT SCHEMA

Return ONLY a JSON array. No markdown, no explanation, no code fences.

[{
  "phrase": "<original candidate phrase>",
  "cleaned_phrase": "<2-6 word standalone version, remove company-specific names, repeat if already clean>",
  "usable": true or false,
  "exclude_reason": "<if usable=false: brief reason>",
  "primary_category": "organizational_purpose" | "good_employer" | "pecuniary" | "job_task" | "unclear",
  "secondary_category": "organizational_purpose" | "good_employer" | "pecuniary" | "job_task" | "unclear" | null,
  "boundary_pair": "purpose/good_employer" | "purpose/task" | "good_employer/pecuniary" | "none",
  "difficulty": "easy" | "medium" | "hard",
  "difficulty_rationale": "<1-2 sentences. For medium/hard: what makes categorization uncertain? Reference identity-based sorting vs employment-condition signaling. Surface vagueness alone is not sufficient.>",
  "context_dependence": "low" | "medium" | "high",
  "context_note": "<if medium/high: how does context change interpretation?>"
}]

**Usable = true** if: 2-6 words, from employer branding language, interpretable without context, not a complete sentence, not a proprietary program name.

**Usable = false** if: needs context to mean anything, names a proprietary internal program, is a complete sentence, is a pure job task or requirement.

---

## WATCH LIST

These types of phrases are often misclassified:

| Phrase type | Common error | Correct call |
|---|---|---|
| "collaborative culture" | classified as good-employer | purpose -- culture is identity-adjacent |
| "career development programs" | classified as purpose | good-employer -- concrete transactional perk |
| "we invest in our people" | easy good-employer | hard purpose/good-employer boundary |
| "innovative work environment" | classified as purpose | may be good-employer if describing working conditions rather than org identity |
| "make an impact" | classified as purpose | may be purpose/task boundary if impact refers to job tasks rather than org mission |
| "people-first culture" | classified as good-employer | purpose -- culture signals shared identity |
| "best place to work" | good-employer | good-employer/purpose boundary -- could signal both employment conditions and organizational identity |
