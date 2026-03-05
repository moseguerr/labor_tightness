import uuid
import random
import string
from django.db import models


class Participant(models.Model):
    """One record per participant session."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participant_code = models.CharField(
        max_length=16, unique=True, blank=True,
        help_text="Auto-generated anonymous ID (e.g. P0001)")
    prolific_id = models.CharField(
        max_length=64, blank=True, db_index=True,
        help_text="Prolific PID from URL params")

    STUDY_CHOICES = [
        ('study2', 'Study 2 — Job Seeker'),
        ('study3', 'Study 3 — Hiring Manager'),
    ]
    study_assignment = models.CharField(max_length=6, choices=STUDY_CHOICES)

    ARM_CHOICES = [
        ('A', 'Arm A — Wages Visible'),
        ('B', 'Arm B — Wages Hidden'),
    ]
    wage_arm = models.CharField(max_length=1, choices=ARM_CHOICES)

    OCCUPATION_CHOICES = [
        ('business_analyst', 'Business Analyst'),
        ('financial_analyst', 'Financial Analyst'),
        ('marketing_analyst', 'Marketing Analyst'),
    ]
    occupation_pool = models.CharField(
        max_length=20, choices=OCCUPATION_CHOICES, blank=True,
        help_text="Which occupation pool this participant sees")

    # Wage counterbalancing: which 2 of the 4 signal types get high wages.
    # Stored as comma-separated signal types, e.g. "purpose_innovation,neutral"
    wage_counterbalance = models.CharField(
        max_length=60, blank=True,
        help_text="Signal types assigned high wages (comma-separated)")

    STATUS_CHOICES = [
        ('created', 'Created'),
        ('consented', 'Consented'),
        ('reading', 'Reading Postings'),
        ('stage1', 'Stage 1 — Rankings'),
        ('stage2', 'Stage 2 — Card Sort'),
        ('stage3', 'Stage 3 — Competition'),
        ('stage4', 'Stage 4 — Bucket Sort'),
        ('individual_diffs', 'Individual Differences'),
        ('demographics', 'Demographics'),
        ('completed', 'Completed'),
        ('withdrawn', 'Withdrawn'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')

    consented = models.BooleanField(default=False)
    consent_timestamp = models.DateTimeField(null=True, blank=True)

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    posting_order_seed = models.IntegerField(null=True, blank=True)

    card_sort_posting = models.ForeignKey(
        'Posting', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='card_sort_participants',
        help_text="Which posting this participant does the card sort on")

    # Quality flags
    attention_checks_passed = models.IntegerField(default=0)
    attention_checks_failed = models.IntegerField(default=0)
    flagged_for_exclusion = models.BooleanField(default=False)

    completion_code = models.CharField(max_length=32, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['study_assignment', 'wage_arm']),
        ]

    def __str__(self):
        return f"{self.participant_code} ({self.study_assignment}/{self.wage_arm}) — {self.status}"

    @property
    def duration_seconds(self):
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def save(self, *args, **kwargs):
        if not self.participant_code:
            self.participant_code = self._generate_code()
        if not self.completion_code:
            self.completion_code = self._generate_completion_code()
        super().save(*args, **kwargs)

    def _generate_code(self):
        for _ in range(10):
            last = (Participant.objects
                    .filter(participant_code__startswith='P')
                    .order_by('-participant_code').first())
            if last:
                try:
                    num = int(last.participant_code[1:]) + 1
                except ValueError:
                    num = 1
            else:
                num = 1
            code = f"P{num:04d}"
            if not Participant.objects.filter(participant_code=code).exists():
                return code
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"P{suffix}"

    def _generate_completion_code(self):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    def get_posting_order(self):
        """Return posting IDs in this participant's randomized order."""
        rng = random.Random(self.posting_order_seed)
        ids = list(
            Posting.objects
            .filter(occupation_pool=self.occupation_pool)
            .values_list('id', flat=True)
        )
        rng.shuffle(ids)
        return ids

    def get_high_wage_signals(self):
        """Return set of signal types assigned high wages for this participant."""
        if not self.wage_counterbalance:
            return set()
        return set(s.strip() for s in self.wage_counterbalance.split(',') if s.strip())


class Posting(models.Model):
    """Fictional job postings for the ranking task. 4 per occupation pool × 3 pools = 12 total."""

    SIGNAL_CHOICES = [
        ('purpose_innovation', 'Purpose — Innovation'),
        ('purpose_social', 'Purpose — Social'),
        ('good_employer', 'Good Employer'),
        ('neutral', 'Neutral'),
    ]
    OCCUPATION_POOL_CHOICES = [
        ('business_analyst', 'Business Analyst'),
        ('financial_analyst', 'Financial Analyst'),
        ('marketing_analyst', 'Marketing Analyst'),
    ]

    occupation_pool = models.CharField(
        max_length=20, choices=OCCUPATION_POOL_CHOICES,
        help_text="Which occupation pool this posting belongs to")
    company_name = models.CharField(max_length=100)
    job_title = models.CharField(max_length=100)
    signal_type = models.CharField(max_length=20, choices=SIGNAL_CHOICES)

    # Salary ranges for high/low wage conditions (determined per participant)
    salary_high_text = models.CharField(
        max_length=50, help_text="Salary text when assigned high wages")
    salary_high_low = models.IntegerField(help_text="Min of high salary range")
    salary_high_high = models.IntegerField(help_text="Max of high salary range")
    salary_low_text = models.CharField(
        max_length=50, help_text="Salary text when assigned low wages")
    salary_low_low = models.IntegerField(help_text="Min of low salary range")
    salary_low_high = models.IntegerField(help_text="Max of low salary range")

    company_intro = models.TextField(
        help_text="Neutral company description paragraph")
    role_description = models.TextField(
        help_text="'The Role' section text")
    signal_section_title = models.CharField(
        max_length=50,
        help_text="e.g. 'Who We Are', 'Our Mission', 'Working at Crestline'")
    signal_section_text = models.TextField(
        help_text="The framing paragraph (purpose/good-employer/neutral)")
    requirements_text = models.TextField()

    class Meta:
        ordering = ['occupation_pool', 'signal_type']
        unique_together = ['occupation_pool', 'signal_type']

    def __str__(self):
        return f"{self.company_name} ({self.occupation_pool}/{self.signal_type})"

    def get_salary_text(self, participant):
        """Return the salary range text based on participant's wage counterbalance."""
        high_signals = participant.get_high_wage_signals()
        if self.signal_type in high_signals:
            return self.salary_high_text
        return self.salary_low_text


class Demographics(models.Model):
    """Standard demographics. All fields optional per IRB."""

    participant = models.OneToOneField(
        Participant, on_delete=models.CASCADE, related_name='demographics')
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=50, blank=True)
    gender_self_describe = models.CharField(max_length=100, blank=True)
    education = models.CharField(max_length=100, blank=True)
    employment_status = models.CharField(max_length=100, blank=True)
    employment_other = models.CharField(max_length=200, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    industry_other = models.CharField(max_length=200, blank=True)
    work_experience_years = models.IntegerField(null=True, blank=True)
    last_job_search = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Demographics"


class IndividualDifferences(models.Model):
    """Job search values, CSR attitudes, corporate skepticism, and context."""

    participant = models.OneToOneField(
        Participant, on_delete=models.CASCADE, related_name='individual_differences')

    # Job Search Values — 10 items, each 1-7
    jsv_salary = models.IntegerField(null=True, blank=True)
    jsv_benefits = models.IntegerField(null=True, blank=True)
    jsv_mission = models.IntegerField(null=True, blank=True)
    jsv_worklife = models.IntegerField(null=True, blank=True)
    jsv_growth = models.IntegerField(null=True, blank=True)
    jsv_security = models.IntegerField(null=True, blank=True)
    jsv_impact = models.IntegerField(null=True, blank=True)
    jsv_autonomy = models.IntegerField(null=True, blank=True)
    jsv_coworkers = models.IntegerField(null=True, blank=True)
    jsv_reputation = models.IntegerField(null=True, blank=True)

    # CSR Attitudes — 4 items, each 1-7
    csr_responsibility = models.IntegerField(null=True, blank=True)
    csr_lower_salary = models.IntegerField(null=True, blank=True)
    csr_usually_mean_it = models.IntegerField(
        null=True, blank=True, help_text="Reverse-scored")
    csr_pay_attention = models.IntegerField(null=True, blank=True)

    # Corporate Skepticism — 3 items, each 1-7
    skep_improve_image = models.IntegerField(null=True, blank=True)
    skep_grain_of_salt = models.IntegerField(null=True, blank=True)
    skep_genuinely_motivated = models.IntegerField(
        null=True, blank=True, help_text="Reverse-coded")

    # Political orientation
    political_orientation = models.IntegerField(
        null=True, blank=True,
        help_text="1=Very liberal, 7=Very conservative, null=Prefer not to say")

    # Employment/financial
    household_income = models.CharField(max_length=50, blank=True)
    job_search_urgency = models.IntegerField(null=True, blank=True, help_text="1-7")
    job_satisfaction = models.IntegerField(null=True, blank=True, help_text="1-7")

    created_at = models.DateTimeField(auto_now_add=True)


# ---------------------------------------------------------------------------
# Study 2: Ranking Task
# ---------------------------------------------------------------------------

class RankingResponse(models.Model):
    """One row per participant × dimension ranking."""

    DIMENSION_CHOICES = [
        ('perceived_pay', 'Perceived Pay'),
        ('employer_quality', 'Employer Quality'),
        ('challenging_rewarding', 'Challenging & Rewarding Work'),
        ('workplace_culture', 'Workplace Culture'),
        ('belief_alignment', 'Belief-Work Alignment'),
        ('mission_identity', 'Mission/Identity Clarity'),
        ('overall_desirability', 'Overall Desirability'),
    ]

    participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name='ranking_responses')
    dimension = models.CharField(max_length=25, choices=DIMENSION_CHOICES)
    dimension_order = models.IntegerField(help_text="Presentation order (1-7)")
    ranking_order = models.JSONField(
        help_text="List of signal_types in rank order, e.g. ['purpose_innovation','neutral',...]")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['participant', 'dimension']
        ordering = ['participant', 'dimension_order']

    def __str__(self):
        return f"{self.participant.participant_code} — {self.dimension} #{self.dimension_order}: {self.ranking_order}"


# ---------------------------------------------------------------------------
# Study 2: Card Sort & Competition
# ---------------------------------------------------------------------------

class CardSortCard(models.Model):
    """A cover-letter statement for the card sort task."""

    TYPE_CHOICES = [
        ('I', 'Identity'),
        ('G', 'Good-Employer'),
        ('C', 'Competence'),
    ]

    card_id = models.CharField(max_length=4, unique=True, help_text="I1, G1, C1, etc.")
    card_type = models.CharField(max_length=1, choices=TYPE_CHOICES)
    card_text = models.CharField(max_length=300)
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return f"[{self.card_id}] {self.card_text[:60]}"


class CardSortResponse(models.Model):
    """One row per participant × stage (card_sort or competition)."""

    STAGE_CHOICES = [
        ('card_sort', 'Card Sort'),
        ('competition', 'Competition'),
    ]

    participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name='card_sort_responses')
    posting = models.ForeignKey(
        Posting, on_delete=models.CASCADE, related_name='card_sort_responses')
    stage = models.CharField(max_length=15, choices=STAGE_CHOICES)
    cards_selected = models.JSONField(
        help_text="List of card_ids selected, e.g. ['I1','C3','G2']")
    selection_order = models.JSONField(
        default=list, blank=True,
        help_text="Order in which cards were clicked")
    keep_original = models.BooleanField(
        default=False,
        help_text="Competition stage: participant kept original selection")
    response_time_ms = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['participant', 'stage']

    def __str__(self):
        action = 'KEPT' if self.keep_original else ','.join(self.cards_selected)
        return f"{self.participant.participant_code} — {self.stage}: {action}"


# ---------------------------------------------------------------------------
# Study 3: Hiring Manager Card Sort & Competition
# ---------------------------------------------------------------------------

class HiringManagerCard(models.Model):
    """A posting-improvement card for the hiring manager card sort (Study 3)."""

    TYPE_CHOICES = [
        ('P', 'Purpose'),
        ('G', 'Good-Employer'),
        ('W', 'Wage'),
        ('T', 'Task'),
    ]

    card_id = models.CharField(max_length=4, unique=True, help_text="HP1, HG1, HW1, HT1, etc.")
    card_type = models.CharField(max_length=1, choices=TYPE_CHOICES)
    card_text = models.CharField(max_length=300)
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return f"[{self.card_id}] {self.card_text[:60]}"


class HiringManagerResponse(models.Model):
    """One row per participant × stage for the hiring manager task (Study 3)."""

    STAGE_CHOICES = [
        ('card_sort', 'Card Sort'),
        ('competition', 'Competition'),
    ]

    participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name='hm_responses')
    posting = models.ForeignKey(
        Posting, on_delete=models.CASCADE, related_name='hm_responses')
    stage = models.CharField(max_length=15, choices=STAGE_CHOICES)
    cards_selected = models.JSONField(
        help_text="card_sort: list of 3 card_ids; competition: list of 0-1 card_ids")
    selection_order = models.JSONField(
        default=list, blank=True,
        help_text="Order in which cards were clicked")
    would_change = models.BooleanField(
        null=True, blank=True,
        help_text="Competition stage: did the participant choose to change? (yes/no)")
    response_time_ms = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['participant', 'stage']

    def __str__(self):
        if self.stage == 'competition' and not self.would_change:
            return f"{self.participant.participant_code} — hm_{self.stage}: NO CHANGE"
        return f"{self.participant.participant_code} — hm_{self.stage}: {','.join(self.cards_selected)}"


# ---------------------------------------------------------------------------
# Study 1: Bucket Sort Game
# ---------------------------------------------------------------------------

class BucketSortPhrase(models.Model):
    """A phrase stimulus for the bucket sort game (Study 1 / Stage 4)."""

    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    BUCKET_CHOICES = [
        ('purpose', 'Organizational purpose'),
        ('good_employer', 'Good employer'),
        ('compensation', 'Compensation & benefits'),
        ('job_tasks', 'Job tasks'),
    ]

    phrase_id = models.CharField(max_length=4, unique=True, help_text="S1-S32")
    phrase_text = models.CharField(max_length=200)
    expected_bucket = models.CharField(max_length=20, choices=BUCKET_CHOICES)
    difficulty = models.CharField(max_length=6, choices=DIFFICULTY_CHOICES)
    boundary_pair = models.CharField(
        max_length=40, blank=True,
        help_text="e.g. 'purpose/good_employer'")
    source = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['phrase_id']

    def __str__(self):
        return f"[{self.phrase_id}] {self.phrase_text} ({self.difficulty})"


class BucketSortResponse(models.Model):
    """One row per phrase catch/miss in the bucket sort game."""

    participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name='bucket_sort_responses')
    phrase = models.ForeignKey(
        BucketSortPhrase, on_delete=models.CASCADE, related_name='responses')
    attempt = models.IntegerField(default=1, help_text="1st, 2nd, 3rd appearance")
    bucket_assigned = models.CharField(
        max_length=20, blank=True, help_text="Which bucket (empty if missed)")
    was_missed = models.BooleanField(default=False)
    time_on_phrase_ms = models.IntegerField(
        null=True, blank=True, help_text="ms from appearance to catch")
    game_elapsed_ms = models.IntegerField(
        null=True, blank=True, help_text="ms since game start")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['participant', 'game_elapsed_ms']

    def __str__(self):
        action = self.bucket_assigned or 'MISSED'
        return f"{self.participant.participant_code} -> {self.phrase.phrase_id} #{self.attempt}: {action}"


class BucketSortReconciliation(models.Model):
    """Post-game reconciliation for phrases classified differently across attempts."""

    RESOLUTION_CHOICES = [
        ('mistake', 'It was a mistake'),
        ('fits_both', 'It fits both categories'),
    ]

    participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name='bucket_reconciliations')
    phrase = models.ForeignKey(
        BucketSortPhrase, on_delete=models.CASCADE, related_name='reconciliations')
    first_bucket = models.CharField(max_length=20)
    second_bucket = models.CharField(max_length=20)
    resolution = models.CharField(max_length=10, choices=RESOLUTION_CHOICES)
    final_bucket = models.CharField(
        max_length=20, blank=True,
        help_text="If mistake, which bucket is correct")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['participant', 'phrase']

    def __str__(self):
        return f"{self.participant.participant_code} -> {self.phrase.phrase_id}: {self.resolution}"
