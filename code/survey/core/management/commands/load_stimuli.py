"""
Load stimuli into the database: 12 fictional job postings (4 per occupation × 3 pools)
and 90 bucket sort phrases.

Usage: python manage.py load_stimuli
       python manage.py load_stimuli --clear
"""
import sys
from pathlib import Path
from django.core.management.base import BaseCommand
from core.models import Posting, BucketSortPhrase, CardSortCard, HiringManagerCard

# Import posting templates from stimuli directory
STIMULI_DIR = Path(__file__).resolve().parent.parent.parent.parent / 'stimuli'
sys.path.insert(0, str(STIMULI_DIR))
from posting_templates import POSTINGS, WAGE_RANGES


# 90 bucket sort phrases — refined category definitions, balanced coverage
BUCKET_SORT_PHRASES = [
    # EASY ANCHORS (16)
    {'phrase_id': 'S01', 'phrase_text': 'mission driven', 'expected_bucket': 'purpose', 'difficulty': 'easy', 'boundary_pair': '', 'source': 'dictionary: meaningful_work / societal values'},
    {'phrase_id': 'S02', 'phrase_text': 'make a real difference', 'expected_bucket': 'purpose', 'difficulty': 'easy', 'boundary_pair': '', 'source': 'dictionary: meaningful_work / impact'},
    {'phrase_id': 'S03', 'phrase_text': 'cutting edge research', 'expected_bucket': 'purpose', 'difficulty': 'easy', 'boundary_pair': '', 'source': 'dictionary: meaningful_work / innovation'},
    {'phrase_id': 'S04', 'phrase_text': 'sustainable future', 'expected_bucket': 'purpose', 'difficulty': 'easy', 'boundary_pair': '', 'source': 'dictionary: environmental_initiatives / sustainability'},
    {'phrase_id': 'S05', 'phrase_text': 'mentorship program', 'expected_bucket': 'good_employer', 'difficulty': 'easy', 'boundary_pair': '', 'source': 'dictionary: career_development / mentorship'},
    {'phrase_id': 'S06', 'phrase_text': 'flexible work schedule', 'expected_bucket': 'good_employer', 'difficulty': 'easy', 'boundary_pair': '', 'source': 'dictionary: job_design / flexible work'},
    {'phrase_id': 'S07', 'phrase_text': 'career development programs', 'expected_bucket': 'good_employer', 'difficulty': 'easy', 'boundary_pair': '', 'source': 'dictionary: career_development / skill development'},
    {'phrase_id': 'S08', 'phrase_text': 'promotion opportunities', 'expected_bucket': 'good_employer', 'difficulty': 'easy', 'boundary_pair': '', 'source': 'dictionary: career_development / progression'},
    {'phrase_id': 'S09', 'phrase_text': 'competitive salary', 'expected_bucket': 'compensation', 'difficulty': 'easy', 'boundary_pair': '', 'source': 'dictionary: pecuniary / additional'},
    {'phrase_id': 'S10', 'phrase_text': '401k match', 'expected_bucket': 'compensation', 'difficulty': 'easy', 'boundary_pair': '', 'source': 'dictionary: pecuniary / retirement'},
    {'phrase_id': 'S11', 'phrase_text': 'performance bonus', 'expected_bucket': 'compensation', 'difficulty': 'easy', 'boundary_pair': '', 'source': 'dictionary: pecuniary / bonus'},
    {'phrase_id': 'S12', 'phrase_text': 'health insurance', 'expected_bucket': 'compensation', 'difficulty': 'easy', 'boundary_pair': '', 'source': 'dictionary: pecuniary / insurance'},
    {'phrase_id': 'S13', 'phrase_text': 'manage cross-functional teams', 'expected_bucket': 'job_tasks', 'difficulty': 'easy', 'boundary_pair': '', 'source': 'dictionary: job_tasks'},
    {'phrase_id': 'S14', 'phrase_text': 'analyze customer data', 'expected_bucket': 'job_tasks', 'difficulty': 'easy', 'boundary_pair': '', 'source': 'dictionary: job_tasks / analysis'},
    {'phrase_id': 'S15', 'phrase_text': 'prepare quarterly reports', 'expected_bucket': 'job_tasks', 'difficulty': 'easy', 'boundary_pair': '', 'source': 'dictionary: job_tasks / reporting'},
    {'phrase_id': 'S16', 'phrase_text': 'oversee daily operations', 'expected_bucket': 'job_tasks', 'difficulty': 'easy', 'boundary_pair': '', 'source': 'dictionary: job_tasks / management'},
    # MEDIUM (28)
    {'phrase_id': 'S17', 'phrase_text': 'pioneering advancements', 'expected_bucket': 'purpose', 'difficulty': 'medium', 'boundary_pair': '', 'source': 'dictionary: meaningful_work / innovation'},
    {'phrase_id': 'S18', 'phrase_text': 'raise the bar', 'expected_bucket': 'purpose', 'difficulty': 'medium', 'boundary_pair': '', 'source': 'dictionary: meaningful_work / innovation'},
    {'phrase_id': 'S19', 'phrase_text': 'breakthrough technologies', 'expected_bucket': 'purpose', 'difficulty': 'medium', 'boundary_pair': '', 'source': 'dictionary: meaningful_work / innovation'},
    {'phrase_id': 'S20', 'phrase_text': 'designing the future', 'expected_bucket': 'purpose', 'difficulty': 'medium', 'boundary_pair': '', 'source': 'dictionary: meaningful_work / innovation'},
    {'phrase_id': 'S21', 'phrase_text': 'shared values', 'expected_bucket': 'purpose', 'difficulty': 'medium', 'boundary_pair': '', 'source': 'dictionary: meaningful_work / societal values'},
    {'phrase_id': 'S22', 'phrase_text': 'positive impact', 'expected_bucket': 'purpose', 'difficulty': 'medium', 'boundary_pair': 'purpose/job_tasks', 'source': 'dictionary: meaningful_work / impact'},
    {'phrase_id': 'S23', 'phrase_text': 'diversity and inclusion', 'expected_bucket': 'purpose', 'difficulty': 'medium', 'boundary_pair': 'purpose/good_employer', 'source': 'dictionary: social_initiatives / DEI'},
    {'phrase_id': 'S24', 'phrase_text': 'social responsibility', 'expected_bucket': 'purpose', 'difficulty': 'medium', 'boundary_pair': '', 'source': 'dictionary: meaningful_work / societal values'},
    {'phrase_id': 'S25', 'phrase_text': 'remote work options', 'expected_bucket': 'good_employer', 'difficulty': 'medium', 'boundary_pair': '', 'source': 'dictionary: job_design / flexible work'},
    {'phrase_id': 'S26', 'phrase_text': 'work-life balance', 'expected_bucket': 'good_employer', 'difficulty': 'medium', 'boundary_pair': '', 'source': 'dictionary: job_design / work-life balance'},
    {'phrase_id': 'S27', 'phrase_text': 'advancement opportunities', 'expected_bucket': 'good_employer', 'difficulty': 'medium', 'boundary_pair': '', 'source': 'dictionary: career_development / progression'},
    {'phrase_id': 'S28', 'phrase_text': 'continuous learning', 'expected_bucket': 'good_employer', 'difficulty': 'medium', 'boundary_pair': '', 'source': 'dictionary: career_development / skill development'},
    {'phrase_id': 'S29', 'phrase_text': 'job security', 'expected_bucket': 'good_employer', 'difficulty': 'medium', 'boundary_pair': '', 'source': 'dictionary: job_design / secure work'},
    {'phrase_id': 'S30', 'phrase_text': 'ownership of projects', 'expected_bucket': 'good_employer', 'difficulty': 'hard', 'boundary_pair': 'good_employer/job_tasks', 'source': 'dictionary: job_design / autonomy'},
    {'phrase_id': 'S31', 'phrase_text': 'stock options', 'expected_bucket': 'compensation', 'difficulty': 'medium', 'boundary_pair': '', 'source': 'dictionary: pecuniary / equity'},
    {'phrase_id': 'S32', 'phrase_text': 'paid time off', 'expected_bucket': 'compensation', 'difficulty': 'medium', 'boundary_pair': 'compensation/good_employer', 'source': 'dictionary: pecuniary / leave'},
    {'phrase_id': 'S33', 'phrase_text': 'education assistance', 'expected_bucket': 'compensation', 'difficulty': 'medium', 'boundary_pair': 'compensation/good_employer', 'source': 'dictionary: pecuniary / tuition'},
    {'phrase_id': 'S34', 'phrase_text': 'comprehensive benefits package', 'expected_bucket': 'compensation', 'difficulty': 'medium', 'boundary_pair': '', 'source': 'dictionary: pecuniary / additional'},
    {'phrase_id': 'S35', 'phrase_text': 'parental leave', 'expected_bucket': 'compensation', 'difficulty': 'medium', 'boundary_pair': 'compensation/good_employer', 'source': 'dictionary: pecuniary / leave'},
    {'phrase_id': 'S36', 'phrase_text': 'annual merit increase', 'expected_bucket': 'compensation', 'difficulty': 'medium', 'boundary_pair': '', 'source': 'dictionary: pecuniary / salary progression'},
    {'phrase_id': 'S37', 'phrase_text': 'profit sharing', 'expected_bucket': 'compensation', 'difficulty': 'medium', 'boundary_pair': '', 'source': 'dictionary: pecuniary / profit sharing'},
    {'phrase_id': 'S38', 'phrase_text': 'coordinate with vendors', 'expected_bucket': 'job_tasks', 'difficulty': 'medium', 'boundary_pair': '', 'source': 'dictionary: job_tasks / coordination'},
    {'phrase_id': 'S39', 'phrase_text': 'conduct market research', 'expected_bucket': 'job_tasks', 'difficulty': 'medium', 'boundary_pair': '', 'source': 'dictionary: job_tasks / analysis'},
    {'phrase_id': 'S40', 'phrase_text': 'develop financial models', 'expected_bucket': 'job_tasks', 'difficulty': 'medium', 'boundary_pair': '', 'source': 'dictionary: job_tasks / financial'},
    {'phrase_id': 'S41', 'phrase_text': 'draft client proposals', 'expected_bucket': 'job_tasks', 'difficulty': 'medium', 'boundary_pair': '', 'source': 'dictionary: job_tasks / writing'},
    {'phrase_id': 'S42', 'phrase_text': 'build dashboards', 'expected_bucket': 'job_tasks', 'difficulty': 'medium', 'boundary_pair': '', 'source': 'dictionary: job_tasks / technical'},
    {'phrase_id': 'S43', 'phrase_text': 'strong analytical skills', 'expected_bucket': 'job_tasks', 'difficulty': 'medium', 'boundary_pair': '', 'source': 'dictionary: job_tasks / requirements'},
    {'phrase_id': 'S44', 'phrase_text': 'project management experience', 'expected_bucket': 'job_tasks', 'difficulty': 'medium', 'boundary_pair': '', 'source': 'dictionary: job_tasks / requirements'},
    # HARD BOUNDARY CASES (25)
    {'phrase_id': 'S45', 'phrase_text': 'we invest in our people', 'expected_bucket': 'purpose', 'difficulty': 'hard', 'boundary_pair': 'purpose/good_employer', 'source': 'assessment instructions example'},
    {'phrase_id': 'S46', 'phrase_text': 'employee-first culture', 'expected_bucket': 'purpose', 'difficulty': 'hard', 'boundary_pair': 'purpose/good_employer', 'source': 'assessment instructions example'},
    {'phrase_id': 'S47', 'phrase_text': 'people are our greatest asset', 'expected_bucket': 'purpose', 'difficulty': 'hard', 'boundary_pair': 'purpose/good_employer', 'source': 'dictionary: organizational_culture / collaborative'},
    {'phrase_id': 'S48', 'phrase_text': 'collaborative team culture', 'expected_bucket': 'purpose', 'difficulty': 'hard', 'boundary_pair': 'purpose/good_employer', 'source': 'dictionary: organizational_culture / collaborative'},
    {'phrase_id': 'S49', 'phrase_text': 'empowering our workforce', 'expected_bucket': 'purpose', 'difficulty': 'hard', 'boundary_pair': 'purpose/good_employer', 'source': 'dictionary: meaningful_work / empowerment'},
    {'phrase_id': 'S50', 'phrase_text': 'open door policy', 'expected_bucket': 'purpose', 'difficulty': 'hard', 'boundary_pair': 'purpose/good_employer', 'source': 'dictionary: organizational_culture / transparency'},
    {'phrase_id': 'S51', 'phrase_text': 'great place to work', 'expected_bucket': 'good_employer', 'difficulty': 'hard', 'boundary_pair': 'purpose/good_employer', 'source': 'dictionary: organizational_culture / workplace recognition'},
    {'phrase_id': 'S52', 'phrase_text': 'nurturing talent', 'expected_bucket': 'good_employer', 'difficulty': 'hard', 'boundary_pair': 'purpose/good_employer', 'source': 'dictionary: career_development / investment'},
    {'phrase_id': 'S53', 'phrase_text': 'inclusive workplace', 'expected_bucket': 'purpose', 'difficulty': 'hard', 'boundary_pair': 'purpose/good_employer', 'source': 'dictionary: social_initiatives / DEI'},
    {'phrase_id': 'S54', 'phrase_text': 'solving global challenges', 'expected_bucket': 'purpose', 'difficulty': 'hard', 'boundary_pair': 'purpose/job_tasks', 'source': 'dictionary: meaningful_work / global challenges'},
    {'phrase_id': 'S55', 'phrase_text': 'creative problem solving', 'expected_bucket': 'job_tasks', 'difficulty': 'hard', 'boundary_pair': 'purpose/job_tasks', 'source': 'dictionary: meaningful_work / innovation'},
    {'phrase_id': 'S56', 'phrase_text': 'driving progress', 'expected_bucket': 'purpose', 'difficulty': 'hard', 'boundary_pair': 'purpose/job_tasks', 'source': 'dictionary: meaningful_work / innovation'},
    {'phrase_id': 'S57', 'phrase_text': 'building the technology of the future', 'expected_bucket': 'purpose', 'difficulty': 'hard', 'boundary_pair': 'purpose/job_tasks', 'source': 'user-provided: non-social purpose'},
    {'phrase_id': 'S58', 'phrase_text': 'technology driven innovation', 'expected_bucket': 'purpose', 'difficulty': 'hard', 'boundary_pair': 'purpose/job_tasks', 'source': 'dictionary: meaningful_work / innovation'},
    {'phrase_id': 'S59', 'phrase_text': 'total rewards', 'expected_bucket': 'compensation', 'difficulty': 'hard', 'boundary_pair': 'good_employer/compensation', 'source': 'compensation industry term'},
    {'phrase_id': 'S60', 'phrase_text': 'employee wellness programs', 'expected_bucket': 'good_employer', 'difficulty': 'hard', 'boundary_pair': 'good_employer/compensation', 'source': 'dictionary: job_design / work-life balance + pecuniary'},
    {'phrase_id': 'S61', 'phrase_text': 'wellness benefits', 'expected_bucket': 'compensation', 'difficulty': 'hard', 'boundary_pair': 'good_employer/compensation', 'source': 'dictionary: pecuniary / additional'},
    {'phrase_id': 'S62', 'phrase_text': 'professional development budget', 'expected_bucket': 'compensation', 'difficulty': 'hard', 'boundary_pair': 'good_employer/compensation', 'source': 'dictionary: pecuniary / tuition + career_development'},
    {'phrase_id': 'S63', 'phrase_text': 'tuition reimbursement', 'expected_bucket': 'compensation', 'difficulty': 'hard', 'boundary_pair': 'good_employer/compensation', 'source': 'dictionary: pecuniary / tuition'},
    {'phrase_id': 'S64', 'phrase_text': 'lead training sessions', 'expected_bucket': 'job_tasks', 'difficulty': 'hard', 'boundary_pair': 'job_tasks/good_employer', 'source': 'dictionary: job_tasks / training'},
    {'phrase_id': 'S65', 'phrase_text': 'mentor junior staff', 'expected_bucket': 'job_tasks', 'difficulty': 'hard', 'boundary_pair': 'job_tasks/good_employer', 'source': 'dictionary: job_tasks / leadership'},
    {'phrase_id': 'S66', 'phrase_text': 'freedom to innovate', 'expected_bucket': 'purpose', 'difficulty': 'hard', 'boundary_pair': 'purpose/good_employer', 'source': 'dictionary: job_design / autonomy'},
    {'phrase_id': 'S67', 'phrase_text': 'manage compensation plans', 'expected_bucket': 'job_tasks', 'difficulty': 'hard', 'boundary_pair': 'job_tasks/compensation', 'source': 'dictionary: job_tasks / HR'},
    {'phrase_id': 'S68', 'phrase_text': 'commission-based earnings', 'expected_bucket': 'compensation', 'difficulty': 'hard', 'boundary_pair': 'job_tasks/compensation', 'source': 'dictionary: pecuniary / variable pay'},
    {'phrase_id': 'S69', 'phrase_text': 'partner with great minds', 'expected_bucket': 'purpose', 'difficulty': 'hard', 'boundary_pair': 'purpose/good_employer', 'source': 'dictionary: meaningful_work / innovation'},
    # ADDITIONS (21)
    {'phrase_id': 'S70', 'phrase_text': 'work with the brightest minds', 'expected_bucket': 'purpose', 'difficulty': 'medium', 'boundary_pair': 'purpose/good_employer', 'source': 'user-provided: non-social purpose'},
    {'phrase_id': 'S71', 'phrase_text': 'shaping future', 'expected_bucket': 'purpose', 'difficulty': 'medium', 'boundary_pair': '', 'source': 'seed-similarity: meaningful_work / innovation'},
    {'phrase_id': 'S72', 'phrase_text': 'disruptive innovation', 'expected_bucket': 'purpose', 'difficulty': 'medium', 'boundary_pair': '', 'source': 'seed-similarity: meaningful_work / innovation'},
    {'phrase_id': 'S73', 'phrase_text': 'purpose driven', 'expected_bucket': 'purpose', 'difficulty': 'easy', 'boundary_pair': '', 'source': 'seed-similarity: meaningful_work / societal values'},
    {'phrase_id': 'S74', 'phrase_text': 'diverse perspectives', 'expected_bucket': 'purpose', 'difficulty': 'medium', 'boundary_pair': 'purpose/good_employer', 'source': 'seed-similarity: organizational_culture / inclusion'},
    {'phrase_id': 'S75', 'phrase_text': 'career path', 'expected_bucket': 'good_employer', 'difficulty': 'easy', 'boundary_pair': '', 'source': 'seed-similarity: career_development / progression'},
    {'phrase_id': 'S76', 'phrase_text': 'learning opportunities', 'expected_bucket': 'good_employer', 'difficulty': 'medium', 'boundary_pair': '', 'source': 'seed-similarity: career_development / mentorship'},
    {'phrase_id': 'S77', 'phrase_text': 'work from home', 'expected_bucket': 'good_employer', 'difficulty': 'easy', 'boundary_pair': '', 'source': 'seed-similarity: job_design / flexible work'},
    {'phrase_id': 'S78', 'phrase_text': 'sign on bonus', 'expected_bucket': 'compensation', 'difficulty': 'easy', 'boundary_pair': '', 'source': 'seed-similarity: pecuniary / additional'},
    {'phrase_id': 'S79', 'phrase_text': 'retirement benefits', 'expected_bucket': 'compensation', 'difficulty': 'medium', 'boundary_pair': '', 'source': 'seed-similarity: pecuniary / retirement'},
    {'phrase_id': 'S80', 'phrase_text': 'relocation assistance', 'expected_bucket': 'compensation', 'difficulty': 'medium', 'boundary_pair': 'compensation/good_employer', 'source': 'seed-similarity: pecuniary / additional'},
    {'phrase_id': 'S81', 'phrase_text': 'develop business strategies', 'expected_bucket': 'job_tasks', 'difficulty': 'medium', 'boundary_pair': '', 'source': 'seed-similarity: job_tasks / tasks'},
    {'phrase_id': 'S82', 'phrase_text': 'design marketing campaigns', 'expected_bucket': 'job_tasks', 'difficulty': 'medium', 'boundary_pair': '', 'source': 'seed-similarity: job_tasks / tasks'},
    {'phrase_id': 'S83', 'phrase_text': 'write technical documentation', 'expected_bucket': 'job_tasks', 'difficulty': 'medium', 'boundary_pair': '', 'source': 'seed-similarity: job_tasks / tasks'},
    {'phrase_id': 'S84', 'phrase_text': 'proven track record', 'expected_bucket': 'job_tasks', 'difficulty': 'easy', 'boundary_pair': '', 'source': 'seed-similarity: job_tasks / requirements'},
    {'phrase_id': 'S85', 'phrase_text': 'work with purpose', 'expected_bucket': 'purpose', 'difficulty': 'hard', 'boundary_pair': 'purpose/good_employer', 'source': 'seed-similarity: boundary case'},
    {'phrase_id': 'S86', 'phrase_text': 'challenging and rewarding', 'expected_bucket': 'purpose', 'difficulty': 'hard', 'boundary_pair': 'purpose/good_employer', 'source': 'seed-similarity: boundary case'},
    {'phrase_id': 'S87', 'phrase_text': 'growth opportunities', 'expected_bucket': 'good_employer', 'difficulty': 'hard', 'boundary_pair': 'good_employer/purpose', 'source': 'seed-similarity: boundary case'},
    {'phrase_id': 'S88', 'phrase_text': 'team building', 'expected_bucket': 'job_tasks', 'difficulty': 'hard', 'boundary_pair': 'job_tasks/purpose', 'source': 'seed-similarity: boundary case'},
    {'phrase_id': 'S89', 'phrase_text': 'recognized and rewarded', 'expected_bucket': 'compensation', 'difficulty': 'hard', 'boundary_pair': 'compensation/purpose', 'source': 'seed-similarity: boundary case'},
    {'phrase_id': 'S90', 'phrase_text': 'meaningful work', 'expected_bucket': 'purpose', 'difficulty': 'hard', 'boundary_pair': 'purpose/good_employer', 'source': 'seed-similarity: meaningful_work / impact'},
]


CARD_SORT_CARDS = [
    {'card_id': 'I1', 'card_type': 'I', 'card_text': 'My passion for this organization\'s mission and what it is working to achieve', 'display_order': 1},
    {'card_id': 'I2', 'card_type': 'I', 'card_text': 'My alignment with this company\'s values and the kind of work they stand for', 'display_order': 2},
    {'card_id': 'I3', 'card_type': 'I', 'card_text': 'My belief in what this organization is building and my desire to be part of it', 'display_order': 3},
    {'card_id': 'I4', 'card_type': 'I', 'card_text': 'My fit with how this team thinks and operates', 'display_order': 4},
    {'card_id': 'G1', 'card_type': 'G', 'card_text': 'My long-term commitment to growing within an organization that invests in its people', 'display_order': 5},
    {'card_id': 'G2', 'card_type': 'G', 'card_text': 'My appreciation for environments that support professional development and work-life balance', 'display_order': 6},
    {'card_id': 'G3', 'card_type': 'G', 'card_text': 'My interest in the specific development opportunities and resources this firm offers', 'display_order': 7},
    {'card_id': 'C1', 'card_type': 'C', 'card_text': 'My technical skills and analytical background relevant to this role', 'display_order': 8},
    {'card_id': 'C2', 'card_type': 'C', 'card_text': 'My track record of delivering results in similar positions', 'display_order': 9},
    {'card_id': 'C3', 'card_type': 'C', 'card_text': 'My academic achievements and relevant coursework', 'display_order': 10},
    {'card_id': 'C4', 'card_type': 'C', 'card_text': 'My leadership experience and ability to work across functions', 'display_order': 11},
    {'card_id': 'C5', 'card_type': 'C', 'card_text': 'My ability to contribute immediately given my prior experience', 'display_order': 12},
]


HM_CARD_SORT_CARDS = [
    {'card_id': 'HP1', 'card_type': 'P', 'card_text': 'Strengthen the description of our mission and what we stand for', 'display_order': 1},
    {'card_id': 'HP2', 'card_type': 'P', 'card_text': 'Add language about the impact this role has on our broader goals', 'display_order': 2},
    {'card_id': 'HP3', 'card_type': 'P', 'card_text': 'Describe the kind of people and values that thrive here', 'display_order': 3},
    {'card_id': 'HP4', 'card_type': 'P', 'card_text': 'Clarify what makes our organization distinct from competitors', 'display_order': 4},
    {'card_id': 'HG1', 'card_type': 'G', 'card_text': 'Add details about career development and learning opportunities', 'display_order': 5},
    {'card_id': 'HG2', 'card_type': 'G', 'card_text': 'Highlight flexibility, hybrid arrangements, or work-life balance', 'display_order': 6},
    {'card_id': 'HG3', 'card_type': 'G', 'card_text': 'Mention mentorship, team support, or internal mobility', 'display_order': 7},
    {'card_id': 'HW1', 'card_type': 'W', 'card_text': 'Add or increase the stated salary range', 'display_order': 8},
    {'card_id': 'HW2', 'card_type': 'W', 'card_text': 'Mention performance bonuses or equity opportunities', 'display_order': 9},
    {'card_id': 'HW3', 'card_type': 'W', 'card_text': 'Highlight the overall compensation and benefits package', 'display_order': 10},
    {'card_id': 'HT1', 'card_type': 'T', 'card_text': 'Make the role description more specific and concrete', 'display_order': 11},
    {'card_id': 'HT2', 'card_type': 'T', 'card_text': 'Clarify what success looks like in this role in the first year', 'display_order': 12},
]


class Command(BaseCommand):
    help = 'Load postings, bucket sort phrases, and card sort cards'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear', action='store_true',
            help='Clear existing stimuli before loading')

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing stimuli...')
            Posting.objects.all().delete()
            BucketSortPhrase.objects.all().delete()
            CardSortCard.objects.all().delete()
            HiringManagerCard.objects.all().delete()

        self._load_postings()
        self._load_bucket_sort_phrases()
        self._load_card_sort_cards()
        self._load_hm_cards()
        self.stdout.write(self.style.SUCCESS('Done.'))

    def _load_postings(self):
        created = 0
        for pool_name, pool_postings in POSTINGS.items():
            wages = WAGE_RANGES[pool_name]
            for post_data in pool_postings:
                _, was_created = Posting.objects.update_or_create(
                    occupation_pool=pool_name,
                    signal_type=post_data['signal_type'],
                    defaults={
                        'company_name': post_data['company_name'],
                        'job_title': post_data['job_title'],
                        'company_intro': post_data['company_intro'],
                        'role_description': post_data['role_description'],
                        'signal_section_title': post_data['signal_section_title'],
                        'signal_section_text': post_data['signal_section_text'],
                        'requirements_text': post_data['requirements_text'],
                        'salary_high_text': wages['high']['text'],
                        'salary_high_low': wages['high']['low'],
                        'salary_high_high': wages['high']['high_val'],
                        'salary_low_text': wages['low']['text'],
                        'salary_low_low': wages['low']['low'],
                        'salary_low_high': wages['low']['high_val'],
                    },
                )
                if was_created:
                    created += 1
        total = sum(len(p) for p in POSTINGS.values())
        self.stdout.write(f'  Postings: {created} created, {total} total')

    def _load_bucket_sort_phrases(self):
        created = 0
        for data in BUCKET_SORT_PHRASES:
            _, was_created = BucketSortPhrase.objects.update_or_create(
                phrase_id=data['phrase_id'],
                defaults={k: v for k, v in data.items()
                          if k != 'phrase_id'})
            if was_created:
                created += 1
        self.stdout.write(
            f'  Bucket sort phrases: {created} created, '
            f'{len(BUCKET_SORT_PHRASES)} total')

    def _load_card_sort_cards(self):
        created = 0
        for data in CARD_SORT_CARDS:
            _, was_created = CardSortCard.objects.update_or_create(
                card_id=data['card_id'],
                defaults={k: v for k, v in data.items() if k != 'card_id'})
            if was_created:
                created += 1
        self.stdout.write(
            f'  Card sort cards: {created} created, '
            f'{len(CARD_SORT_CARDS)} total')

    def _load_hm_cards(self):
        created = 0
        for data in HM_CARD_SORT_CARDS:
            _, was_created = HiringManagerCard.objects.update_or_create(
                card_id=data['card_id'],
                defaults={k: v for k, v in data.items() if k != 'card_id'})
            if was_created:
                created += 1
        self.stdout.write(
            f'  HM cards: {created} created, '
            f'{len(HM_CARD_SORT_CARDS)} total')
