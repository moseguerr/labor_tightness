"""
Load stimuli into the database: phrases from JSON, practice items, attention checks,
and 6 fictional job postings from IRB-approved materials.

Usage: python manage.py load_stimuli
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings

from core.models import Phrase, JobPosting


# ── Practice items (IRB Section 1c) ──────────────────────────────────────

PRACTICE_ITEMS = [
    {
        'phrase_text': '401(k) retirement plan',
        'context_text': 'We offer a comprehensive benefits package including a <strong>401(k) retirement plan</strong> with company match.',
        'correct_categories': ['pay_benefits'],
        'feedback_text': 'This phrase describes a specific financial benefit (a retirement savings plan). It fits the "Pay, benefits, or financial perks" category.',
        'display_order': 1,
    },
    {
        'phrase_text': 'manage and coordinate project timelines',
        'context_text': 'The successful candidate will <strong>manage and coordinate project timelines</strong> across multiple departments.',
        'correct_categories': ['job_tasks'],
        'feedback_text': 'This phrase describes an activity the employee would perform on the job. It fits the "Job tasks, duties, or responsibilities" category.',
        'display_order': 2,
    },
    {
        'phrase_text': 'committed to reducing our carbon footprint by 50%',
        'context_text': 'As an organization, we are deeply <strong>committed to reducing our carbon footprint by 50%</strong> over the next decade.',
        'correct_categories': ['mission_values'],
        'feedback_text': 'This phrase describes the company\'s environmental commitment. It fits the "Mission, values, or social/environmental impact" category.',
        'display_order': 3,
    },
    {
        'phrase_text': 'minimum 3 years of experience in digital marketing',
        'context_text': 'Qualified applicants must have a <strong>minimum 3 years of experience in digital marketing</strong> and hold a relevant certification.',
        'correct_categories': ['job_requirements'],
        'feedback_text': 'This phrase specifies what the candidate needs (experience and credentials). It fits the "Job requirements or qualifications" category.',
        'display_order': 4,
    },
    {
        'phrase_text': 'flexible work-from-home schedule and generous parental leave',
        'context_text': 'Team members enjoy a <strong>flexible work-from-home schedule and generous parental leave</strong> to support work-life balance.',
        'correct_categories': ['treats_well', 'pay_benefits'],
        'feedback_text': 'This phrase could fit two categories: the flexible schedule signals a supportive workplace ("The company treats employees well"), while the parental leave is a specific benefit ("Pay, benefits, or financial perks"). Checking both is correct \u2014 some phrases genuinely belong to more than one category.',
        'display_order': 5,
    },
]


# ── Attention check anchors (IRB Section 1e) ─────────────────────────────

ATTENTION_CHECKS = [
    {
        'phrase_text': 'medical, dental, and vision coverage',
        'context_text': 'Full-time employees receive <strong>medical, dental, and vision coverage</strong> starting on their first day.',
        'correct_categories': ['pay_benefits'],
        'display_order': 1,
    },
    {
        'phrase_text': 'preparing quarterly financial statements and reconciling accounts payable',
        'context_text': 'The role involves <strong>preparing quarterly financial statements and reconciling accounts payable</strong>.',
        'correct_categories': ['job_tasks'],
        'display_order': 2,
    },
    {
        'phrase_text': 'current CPA license',
        'context_text': 'Applicants must hold a <strong>current CPA license</strong> and have at least five years of audit experience.',
        'correct_categories': ['job_requirements'],
        'display_order': 3,
    },
    {
        'phrase_text': 'pledged to achieve carbon neutrality by 2030',
        'context_text': 'Our company has <strong>pledged to achieve carbon neutrality by 2030</strong> and actively supports reforestation projects worldwide.',
        'correct_categories': ['mission_values'],
        'display_order': 4,
    },
    {
        'phrase_text': "named one of Fortune's Best Places to Work",
        'context_text': 'We have been <strong>named one of Fortune\'s Best Places to Work</strong> for five consecutive years thanks to our culture of trust and recognition.',
        'correct_categories': ['treats_well'],
        'display_order': 5,
    },
]


# ── Job postings (IRB Section 2b) ────────────────────────────────────────

RESPONSIBILITIES = [
    'Develop and execute multi-channel marketing campaigns, including email, social media, and paid advertising',
    'Analyze campaign performance data, prepare monthly reports, and recommend optimizations',
    'Coordinate with product and sales teams to align marketing strategy with business objectives',
]

BENEFITS_TEXT = 'Benefits include health, dental, and vision insurance; 401(k) with employer match; and paid time off.'

JOB_POSTINGS = [
    {
        'condition_label': 'A',
        'company_name': 'Meridian Partners',
        'company_tagline': 'A purpose-driven consulting firm dedicated to helping communities thrive',
        'framing': 'purpose',
        'salary_level': 'high',
        'salary_amount': 78000,
        'company_description': (
            'At Meridian Partners, our work is driven by a commitment to building more sustainable '
            'and equitable communities. Every project we take on is guided by the belief that business '
            'can be a force for positive social and environmental change. We measure our success not '
            'just in revenue, but in the lasting impact we create for the people and places we serve.'
        ),
    },
    {
        'condition_label': 'B',
        'company_name': 'Crestline Industries',
        'company_tagline': 'A mission-focused consumer goods company committed to social and environmental responsibility',
        'framing': 'purpose',
        'salary_level': 'low',
        'salary_amount': 52000,
        'company_description': (
            'At Crestline Industries, we believe that every business decision should reflect our '
            'responsibility to people and the planet. From our ethical sourcing practices to our '
            'partnerships with local nonprofits, we are driven by a mission to create products that '
            'do good in the world. Our employees join us because they want their work to matter '
            'beyond the bottom line.'
        ),
    },
    {
        'condition_label': 'C',
        'company_name': 'Bridgewell & Co.',
        'company_tagline': 'A mid-size marketing services firm recognized for its outstanding workplace culture',
        'framing': 'good_employer',
        'salary_level': 'high',
        'salary_amount': 78000,
        'company_description': (
            'At Bridgewell & Co., we are proud to be consistently recognized as a top workplace. '
            'We invest in our people through one-on-one mentorship, flexible scheduling, and a '
            'collaborative culture where every voice is heard. Our leadership team maintains an '
            'open-door policy, and we celebrate achievements at every level. We believe that when '
            'employees feel supported and valued, they do their best work.'
        ),
    },
    {
        'condition_label': 'D',
        'company_name': 'Novalink Group',
        'company_tagline': 'A growing analytics company known for investing in its employees',
        'framing': 'good_employer',
        'salary_level': 'low',
        'salary_amount': 52000,
        'company_description': (
            'At Novalink Group, we believe our people are our greatest asset. We offer structured '
            'career development pathways, regular feedback and coaching, and a psychologically safe '
            'environment where new ideas are welcomed. Our team-first culture has earned us '
            'recognition as one of the best mid-size employers in the region. We are committed to '
            'your long-term professional growth and well-being.'
        ),
    },
    {
        'condition_label': 'E',
        'company_name': 'Hearthstone Solutions',
        'company_tagline': 'A mid-size consumer products firm serving retail and e-commerce channels nationwide',
        'framing': 'neutral',
        'salary_level': 'high',
        'salary_amount': 78000,
        'company_description': (
            'Founded in 2008, Hearthstone Solutions is a consumer products company headquartered '
            'in the Washington, DC metro area. The company serves retail and e-commerce clients '
            'across the United States and employs approximately 850 people across four regional '
            'offices. The marketing department supports product launches, market research, and '
            'customer engagement initiatives.'
        ),
    },
    {
        'condition_label': 'F',
        'company_name': 'Thornbury Corp.',
        'company_tagline': 'An established business services firm with nationwide operations',
        'framing': 'neutral',
        'salary_level': 'low',
        'salary_amount': 52000,
        'company_description': (
            'Thornbury Corp. is a business services company founded in 2003 with headquarters in '
            'Arlington, Virginia. The company provides marketing analytics and consulting services '
            'to clients in the retail, healthcare, and financial services sectors. Thornbury employs '
            'approximately 600 staff members and has maintained steady growth over the past decade.'
        ),
    },
]


class Command(BaseCommand):
    help = 'Load phrases from JSON, practice items, attention checks, and job postings into the DB'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear', action='store_true',
            help='Clear existing stimuli before loading (idempotent reload)')

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing stimuli...')
            Phrase.objects.all().delete()
            JobPosting.objects.all().delete()

        self._load_phrases()
        self._load_practice_items()
        self._load_attention_checks()
        self._load_job_postings()

        self.stdout.write(self.style.SUCCESS('Done.'))

    def _load_phrases(self):
        """Load main phrases from phrases_raw.json."""
        json_path = Path(settings.STIMULI_DIR) / 'phrases_raw.json'
        if not json_path.exists():
            self.stdout.write(self.style.WARNING(
                f'phrases_raw.json not found at {json_path}. Skipping main phrases.'))
            return

        with open(json_path) as f:
            data = json.load(f)

        created = 0
        for item in data:
            phrase_text = item['phrase']
            context = item['context']
            # Bold the target phrase in context for display
            context_html = context.replace(
                phrase_text,
                f'<strong class="phrase-highlight">{phrase_text}</strong>',
                1)

            _, was_created = Phrase.objects.update_or_create(
                phrase_text=phrase_text,
                context_text=context_html,
                item_type='main',
                defaults={
                    'dict_category': item.get('dict_category', ''),
                    'dict_subcategory': item.get('dict_subcategory', ''),
                    'irb_category': item.get('irb_category', ''),
                    'is_ambiguous': item.get('is_ambiguous', False),
                    'is_active': True,
                })
            if was_created:
                created += 1

        self.stdout.write(f'  Main phrases: {created} created, {len(data)} total in JSON')

    def _load_practice_items(self):
        """Load 5 practice items with feedback from IRB materials."""
        created = 0
        for item in PRACTICE_ITEMS:
            _, was_created = Phrase.objects.update_or_create(
                phrase_text=item['phrase_text'],
                item_type='practice',
                defaults={
                    'context_text': item['context_text'],
                    'correct_categories': item['correct_categories'],
                    'feedback_text': item['feedback_text'],
                    'display_order': item['display_order'],
                    'irb_category': item['correct_categories'][0],
                    'is_active': True,
                })
            if was_created:
                created += 1

        self.stdout.write(f'  Practice items: {created} created, {len(PRACTICE_ITEMS)} total')

    def _load_attention_checks(self):
        """Load 5 attention check anchors from IRB materials."""
        created = 0
        for item in ATTENTION_CHECKS:
            _, was_created = Phrase.objects.update_or_create(
                phrase_text=item['phrase_text'],
                item_type='attention',
                defaults={
                    'context_text': item['context_text'],
                    'correct_categories': item['correct_categories'],
                    'display_order': item['display_order'],
                    'irb_category': item['correct_categories'][0],
                    'is_active': True,
                })
            if was_created:
                created += 1

        self.stdout.write(f'  Attention checks: {created} created, {len(ATTENTION_CHECKS)} total')

    def _load_job_postings(self):
        """Load 6 fictional job postings from IRB materials."""
        created = 0
        for posting in JOB_POSTINGS:
            _, was_created = JobPosting.objects.update_or_create(
                condition_label=posting['condition_label'],
                defaults={
                    'company_name': posting['company_name'],
                    'company_tagline': posting['company_tagline'],
                    'framing': posting['framing'],
                    'salary_level': posting['salary_level'],
                    'salary_amount': posting['salary_amount'],
                    'responsibilities': RESPONSIBILITIES,
                    'company_description': posting['company_description'],
                    'benefits_text': BENEFITS_TEXT,
                })
            if was_created:
                created += 1

        self.stdout.write(f'  Job postings: {created} created, {len(JOB_POSTINGS)} total')
