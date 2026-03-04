# Prewritten Employer Branding Sections — Study 3 (Hiring Manager Posting Builder)

These are prewritten employer branding sections for a planned extension of Study 3, in which hiring managers assemble a job posting by selecting from modular sections. Each section is 1-2 sentences, represents one signal type, and is drawn from the project's validated dictionary phrases. The sections are designed to be embeddable in a fictional job posting without requiring surrounding context.

The five signal types map to the card sort taxonomy used in Study 3 Stages 2 and 3 (see `study3_card_sort_screen.md`): Purpose (P), Good-Employer (G), Wage/Compensation (W), Task/Role (T), with Purpose split into social and innovation variants.

---

## Section 1: PURPOSE-SOCIAL

**Final version:**

Our mission is to create lasting, positive change in the communities we serve. We are looking for people who share our belief that business can be a force for reducing inequality and building a more equitable future.

**Source phrases:**
- "mission driven" / "corporate mission" -- meaningful_work / alignment with societal values
- "create positive change" / "lasting impact" -- meaningful_work / opportunities to make an impact
- "reducing inequality" -- meaningful_work / roles tied to solving global challenges
- "shared values" / "share values" -- meaningful_work / alignment with societal values
- "build stronger communities" / "strengthening communities" -- meaningful_work / opportunities to make an impact
- "greater good" / "double bottom line" -- meaningful_work / alignment with societal values

**Register notes:** DRAFT -- PENDING LIGHTCAST REFINEMENT. Register modeled on Posting B (Bridgewell Financial), which uses similar mission-driven language in a warm, declarative tone ("Our mission is to..."). The Lightcast merged dataset (`full_dataset.parquet`) contains only structured variables (226 columns: firm identifiers, occupation codes, wage data, dictionary count/proportion variables, labor market indicators). Raw job posting text (`JobText`) is available only in the per-month processed parquets on the Georgetown server (`/global/home/pc_moseguera/data/Burning Glass 2/`) and in XML files on the external drive (`/Volumes/Expansion/All server/data/Burning Glass 2/XML/`), both too large to process here. Lightcast refinement should be performed when server access is available.

---

## Section 2: PURPOSE-INNOVATION

**Final version:**

We are pioneering the next generation of solutions in our industry, and this role puts you at the frontier of that work. We recruit people who are energized by breakthrough problems and want to help build something that has not been done before.

**Source phrases:**
- "pioneering advancements" / "pioneering" -- meaningful_work / working on innovation
- "next gen solutions" -- meaningful_work / working on innovation
- "breakthrough technologies" -- meaningful_work / working on innovation
- "cutting edge research" -- meaningful_work / working on innovation
- "designing the future" / "help build future" -- meaningful_work / working on innovation
- "creative problem solving" -- meaningful_work / working on innovation
- "innovative roles" -- meaningful_work / working on innovation

**Register notes:** DRAFT -- PENDING LIGHTCAST REFINEMENT. Register modeled on Postings A (Vantage Strategy Group) and D (Novalink Group), which use frontier/pioneering language in an aspirational but concrete tone ("We are redefining...", "We are building the future of..."). Avoids vague Silicon Valley phrasing; anchors innovation to the specific work rather than abstract disruption.

---

## Section 3: GOOD-EMPLOYER

**Final version:**

Every new hire is paired with a senior mentor, and we offer a dedicated professional development budget, a clear annual promotion review, and flexible hybrid work arrangements. We believe investing in our people's growth is the foundation of everything we do well.

**Source phrases:**
- "mentorship" / "mentor programs" -- career_development_opportunities / mentorship and coaching
- "professional development" / "skill development" -- career_development_opportunities / skill development programs
- "career progression" / "promotion tracks" / "clear advancement paths" -- career_development_opportunities / clear career progression paths
- "flexible hours" / "hybrid schedule" / "flexible workplace" -- job_design_characteristics / flexible work arrangements
- "work life balance" -- job_design_characteristics / work life balance initiatives

**Register notes:** DRAFT -- PENDING LIGHTCAST REFINEMENT. Register modeled on Posting C (Crestline Industries), which lists concrete benefits in a transactional, itemized style ("We offer a structured mentorship program... a clear promotion track... flexible hybrid work arrangements"). Good-employer sections should feel like a tangible value proposition with named programs and specific details, not aspirational identity language.

---

## Section 4: COMPENSATION

**Final version:**

This position offers a competitive salary, annual performance bonuses, equity participation, and a comprehensive benefits package including 401(k) matching, health and dental coverage, and generous paid time off.

**Source phrases:**
- "bonus" -- pecuniary_benefits / additional benefits
- "stock options" / "equity grants" / "employee stock ownership" -- pecuniary_benefits / stock options or equity grants
- "401k" / "retirement" -- pecuniary_benefits / retirement plans
- "health insurance" / "dental insurance" -- pecuniary_benefits / insurance benefits
- "paid time off" / "vacation" -- pecuniary_benefits / paid time off
- "competitive benefits" / "comprehensive benefits" -- pecuniary_benefits / additional benefits
- "profit sharing" -- pecuniary_benefits / profit sharing

**Register notes:** DRAFT -- PENDING LIGHTCAST REFINEMENT. Register uses standard compensation boilerplate common in job postings: itemized list of monetary and near-monetary benefits in a single sentence. Deliberately functional and transactional -- no identity claims, no employer investment framing, just direct monetary signals. The phrase "competitive salary" is a widely used convention that signals market-rate or above without committing to a specific number.

---

## Section 5: NEUTRAL/TASK

**Final version:**

You will manage cross-functional project timelines, prepare analytical reports for senior leadership, and coordinate with internal teams to ensure deliverables meet quality and deadline requirements.

**Source phrases:** None from project dictionaries. This section is deliberately composed of generic job task language that does not map to any dictionary category. The terms ("manage," "prepare," "coordinate," "reports," "deliverables," "timelines") are drawn from standard operational job description boilerplate. While `job_tasks_requirements` in `refine_dictionaries.py` lists generic verbs like "manage," "analyze," "report," "coordinate," these are functional role descriptors excluded from the construct by design.

**Register notes:** DRAFT -- PENDING LIGHTCAST REFINEMENT. Register modeled on Posting E (Thornbury Corp), which uses flat, informational prose with no signal language ("You will monitor daily throughput metrics... identify bottlenecks... develop process improvement recommendations"). The neutral section should feel like role mechanics -- what the person does day-to-day -- with no implicit claims about identity, values, investment, or compensation.

---

## Draft Alternates (Not Selected)

The drafting process produced two versions per signal type. Below are the alternate versions not selected as finals, preserved for reference.

### PURPOSE-SOCIAL — Alternate (formal register)

We are committed to advancing equitable outcomes in the communities where we operate, and we seek professionals whose work reflects a dedication to social impact and sustainable development.

### PURPOSE-INNOVATION — Alternate (formal register)

This organization leads applied research and development at the frontier of our field. The role offers direct involvement in technology-driven innovation that is shaping the next generation of industry practice.

### GOOD-EMPLOYER — Alternate (formal register)

The organization provides structured career development including mentorship, a dedicated training budget, transparent promotion criteria, and flexible work arrangements designed to support long-term professional growth.

### COMPENSATION — Alternate (warm register)

We back our commitment to talent with a compensation package that includes a strong base salary, performance-based bonuses, equity opportunities, and a full suite of benefits from health coverage to retirement matching and paid time off.

### NEUTRAL/TASK — Alternate (formal register)

Responsibilities include developing standardized reports, maintaining project documentation, tracking key performance indicators, and liaising with departmental stakeholders on operational priorities.

---

## Integration Notes

- **`phrases_candidate.csv` does not exist yet.** Study 1 phrase-level difficulty ratings (from the checkbox classification task) are not available. When Study 1 data is collected, phrase difficulty scores should be cross-referenced with the source phrases listed above to verify that the dictionary terms anchoring each section are reliably classified by participants. If any anchor phrase has a low classification accuracy in Study 1, the corresponding section wording should be revised.

- **Lightcast refinement was not performed.** The merged dataset (`full_dataset.parquet`) contains 226 structured columns but no raw posting text. Raw text is in per-month processed parquets on the Georgetown server and in XML archives on the external drive. When server access is available, sample real postings by NAICS code (813/621-622 for social, 511-541 for innovation, 52/44-45 for good-employer, 52/336 for compensation) and compare register and phrasing against these draft sections. Key things to check: (1) whether real employers use the warm or formal register more often, (2) whether the sentence length and specificity level match real postings, (3) whether any dictionary phrases appear stilted in context.

- **Card sort alignment.** These five sections correspond to the four card types in the Study 3 card sort (P, G, W, T), with the P type split into social (Section 1) and innovation (Section 2). In a posting builder task, participants would select from these sections to assemble a posting. The card sort data from Study 3 Stages 2-3 will reveal which signal types hiring managers reach for under baseline and competitive conditions, which should inform which sections are offered and how many a participant can select.
