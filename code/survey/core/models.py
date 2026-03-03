import uuid
from django.db import models
from django.utils import timezone


class Participant(models.Model):
    """One record per participant session. Anonymous — no names collected."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participant_code = models.CharField(
        max_length=16, unique=True,
        help_text="Auto-generated anonymous ID (e.g. P0001)")
    external_id = models.CharField(
        max_length=64, blank=True, db_index=True,
        help_text="Optional external ID (for future Prolific integration)")

    SESSION_TYPES = [
        ('study1', 'Study 1 Only'),
        ('study2', 'Study 2 Only'),
        ('combined', 'Combined Session'),
    ]
    session_type = models.CharField(max_length=10, choices=SESSION_TYPES)

    STATUS_CHOICES = [
        ('consented', 'Consented'),
        ('in_study1', 'In Study 1'),
        ('in_study2', 'In Study 2'),
        ('in_demographics', 'In Demographics'),
        ('completed', 'Completed'),
        ('withdrawn', 'Withdrawn'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='consented')

    consented = models.BooleanField(default=False)
    consent_timestamp = models.DateTimeField(null=True, blank=True)

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Randomization seeds for reproducibility
    phrase_seed = models.IntegerField(null=True, blank=True)
    posting_order_seed = models.IntegerField(null=True, blank=True)

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
            models.Index(fields=['started_at']),
        ]

    def __str__(self):
        return f"{self.participant_code} ({self.session_type}) - {self.status}"

    @property
    def duration_seconds(self):
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def save(self, *args, **kwargs):
        if not self.participant_code:
            # Auto-generate sequential code
            last = Participant.objects.order_by('-participant_code').first()
            if last and last.participant_code.startswith('P'):
                try:
                    num = int(last.participant_code[1:]) + 1
                except ValueError:
                    num = 1
            else:
                num = 1
            self.participant_code = f"P{num:04d}"
        super().save(*args, **kwargs)


class Phrase(models.Model):
    """A phrase stimulus for Study 1. Loaded from phrases_raw.json."""

    ITEM_TYPES = [
        ('main', 'Main Item'),
        ('practice', 'Practice Item'),
        ('attention', 'Attention Check'),
    ]

    phrase_text = models.TextField(help_text="The bolded phrase shown to participant")
    context_text = models.TextField(help_text="1-2 sentence job posting context")
    item_type = models.CharField(max_length=10, choices=ITEM_TYPES, default='main')

    # Source metadata (from extraction)
    dict_category = models.CharField(max_length=64, blank=True)
    dict_subcategory = models.CharField(max_length=128, blank=True)
    irb_category = models.CharField(
        max_length=32, blank=True,
        help_text="Expected correct IRB category")

    # For practice and attention checks
    correct_categories = models.JSONField(
        default=list, blank=True,
        help_text="List of correct category slugs")
    feedback_text = models.TextField(
        blank=True, help_text="Feedback shown after practice items")

    is_active = models.BooleanField(default=True)
    is_ambiguous = models.BooleanField(default=False)
    display_order = models.IntegerField(
        default=0, help_text="Order within practice/attention sets")

    class Meta:
        ordering = ['item_type', 'display_order']

    def __str__(self):
        return f"[{self.item_type}] {self.phrase_text[:50]}"


class Study1Response(models.Model):
    """One row per phrase classification by a participant."""

    participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name='study1_responses')
    phrase = models.ForeignKey(
        Phrase, on_delete=models.CASCADE, related_name='responses')
    presentation_order = models.IntegerField(
        help_text="Position in this participant's sequence (1-indexed)")

    # Which categories the participant checked (multi-select)
    selected_mission_values = models.BooleanField(default=False)
    selected_treats_well = models.BooleanField(default=False)
    selected_pay_benefits = models.BooleanField(default=False)
    selected_job_tasks = models.BooleanField(default=False)
    selected_job_requirements = models.BooleanField(default=False)
    selected_none_unsure = models.BooleanField(default=False)

    displayed_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    is_correct = models.BooleanField(null=True, blank=True)

    class Meta:
        unique_together = ['participant', 'phrase']
        ordering = ['participant', 'presentation_order']

    def __str__(self):
        return f"{self.participant.participant_code} -> {self.phrase.phrase_text[:30]}"

    @property
    def time_spent_seconds(self):
        if self.responded_at and self.displayed_at:
            return (self.responded_at - self.displayed_at).total_seconds()
        return None

    @property
    def selected_categories(self):
        selected = []
        if self.selected_mission_values:
            selected.append('mission_values')
        if self.selected_treats_well:
            selected.append('treats_well')
        if self.selected_pay_benefits:
            selected.append('pay_benefits')
        if self.selected_job_tasks:
            selected.append('job_tasks')
        if self.selected_job_requirements:
            selected.append('job_requirements')
        if self.selected_none_unsure:
            selected.append('none_unsure')
        return selected


class Study1PostTask(models.Model):
    """Post-task questions after Study 1 classification."""

    participant = models.OneToOneField(
        Participant, on_delete=models.CASCADE, related_name='study1_post_task')
    confidence = models.IntegerField(help_text="1-7: How confident in classifications")
    confusion_text = models.TextField(
        blank=True, help_text="Open text: categories confusing or hard to tell apart")
    familiarity = models.IntegerField(help_text="1-7: How familiar with reading job postings")
    created_at = models.DateTimeField(auto_now_add=True)


class JobPosting(models.Model):
    """The 6 fictional job postings for Study 2. Fixed IRB content."""

    FRAMING_CHOICES = [
        ('purpose', 'Purpose / Mission-driven'),
        ('good_employer', 'Good Employer'),
        ('neutral', 'Neutral / Control'),
    ]
    SALARY_CHOICES = [
        ('high', 'High ($78,000)'),
        ('low', 'Low ($52,000)'),
    ]

    condition_label = models.CharField(
        max_length=1, help_text="A-F condition label from IRB design matrix")
    company_name = models.CharField(max_length=100)
    company_tagline = models.CharField(
        max_length=200, blank=True, help_text="Italicized subtitle under company name")
    framing = models.CharField(max_length=15, choices=FRAMING_CHOICES)
    salary_level = models.CharField(max_length=4, choices=SALARY_CHOICES)
    salary_amount = models.IntegerField(help_text="Annual salary in dollars")
    job_title = models.CharField(max_length=100, default="Marketing Analyst")
    location = models.CharField(max_length=100, default="Washington, DC metro area")

    responsibilities = models.JSONField(
        default=list, help_text="List of responsibility bullet points")
    company_description = models.TextField(
        help_text="The framing paragraph (purpose/good-employer/neutral)")
    benefits_text = models.TextField(help_text="Benefits line")

    class Meta:
        ordering = ['condition_label']

    def __str__(self):
        return f"[{self.condition_label}] {self.company_name} ({self.framing}/{self.salary_level})"


class PostingViewRecord(models.Model):
    """Records that a participant viewed a specific posting."""

    participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name='posting_views')
    posting = models.ForeignKey(
        JobPosting, on_delete=models.CASCADE, related_name='views')
    presentation_order = models.IntegerField(
        help_text="Order this posting was shown (1-6)")
    viewed_at = models.DateTimeField(null=True, blank=True)
    time_spent_seconds = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ['participant', 'posting']
        ordering = ['participant', 'presentation_order']


class Study2ManipulationCheck(models.Model):
    """4 manipulation check questions after viewing all 6 postings."""

    participant = models.OneToOneField(
        Participant, on_delete=models.CASCADE, related_name='manipulation_checks')
    most_mission = models.CharField(max_length=100)
    most_workplace = models.CharField(max_length=100)
    highest_salary = models.CharField(max_length=100)
    job_title_check = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)


class Study2Ranking(models.Model):
    """One row per ranking dimension per participant."""

    DIMENSION_CHOICES = [
        ('attractiveness', 'Application Attractiveness'),
        ('sincerity', 'Perceived Sincerity'),
        ('employee_treatment', 'Employee Treatment'),
        ('accept_lower_pay', 'Willingness to Accept Lower Pay'),
        ('instrumentality', 'Perceived Instrumentality'),
    ]

    participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name='rankings')
    dimension = models.CharField(max_length=30, choices=DIMENSION_CHOICES)
    ranking_order = models.JSONField(
        help_text="Ordered list of company names, position 0 = rank 1")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['participant', 'dimension']


class Study2PostRanking(models.Model):
    """Post-ranking follow-up questions about the top-ranked company."""

    participant = models.OneToOneField(
        Participant, on_delete=models.CASCADE, related_name='post_ranking')
    top_company = models.CharField(
        max_length=100, help_text="Auto-filled from attractiveness rank #1")
    explanation_text = models.TextField(
        blank=True, help_text="Why this posting stood out")
    min_acceptable_salary = models.IntegerField(
        null=True, blank=True,
        help_text="Minimum salary to accept at top-ranked company")

    # Person-Organization Fit (3 items, 7-point Likert)
    po_fit_values = models.IntegerField(
        null=True, blank=True, help_text="1-7: Personal values aligned")
    po_fit_belong = models.IntegerField(
        null=True, blank=True, help_text="1-7: Would fit in well")
    po_fit_care = models.IntegerField(
        null=True, blank=True, help_text="1-7: Reflects what I care about")
    created_at = models.DateTimeField(auto_now_add=True)


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


class Demographics(models.Model):
    """Standard demographics collected at the end. All optional per IRB."""

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
