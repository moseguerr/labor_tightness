import json
import random
import time
import uuid
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView
from django.utils import timezone

from .models import (
    Participant, Posting, Demographics, IndividualDifferences,
    RankingResponse, CardSortCard, CardSortResponse,
    HiringManagerCard, HiringManagerResponse,
    BucketSortPhrase, BucketSortResponse, BucketSortReconciliation,
)


# ---------------------------------------------------------------------------
# Flow control mixin
# ---------------------------------------------------------------------------

class SurveyFlowMixin:
    """Manages participant session state and enforces linear flow."""
    requires_participant = True
    requires_consent = True

    def get_participant(self):
        participant_id = self.request.session.get('participant_id')
        if not participant_id:
            return None
        try:
            return Participant.objects.get(id=participant_id)
        except Participant.DoesNotExist:
            return None

    def dispatch(self, request, *args, **kwargs):
        if not self.requires_participant:
            return super().dispatch(request, *args, **kwargs)
        participant = self.get_participant()
        if not participant:
            return redirect('core:landing')
        if self.requires_consent and not participant.consented:
            return redirect('core:consent')
        return super().dispatch(request, *args, **kwargs)

    def update_status(self, participant, status):
        participant.status = status
        participant.save(update_fields=['status'])


# ---------------------------------------------------------------------------
# Entry flow
# ---------------------------------------------------------------------------

class LandingView(SurveyFlowMixin, TemplateView):
    template_name = 'landing.html'
    requires_participant = False

    @staticmethod
    def _generate_user_id():
        """Generate a unique 8-character alphanumeric user ID."""
        import string as _string
        for _ in range(20):
            uid = ''.join(random.choices(_string.ascii_uppercase + _string.digits, k=8))
            if not Participant.objects.filter(user_id=uid).exists():
                return uid
        return uuid.uuid4().hex[:12].upper()

    def post(self, request, *args, **kwargs):
        user_id = self._generate_user_id()

        # Randomly assign participant to study2 (job seeker) or study3 (hiring manager)
        study = random.choice(['study2', 'study3'])

        prolific_id = request.GET.get('PROLIFIC_PID', '')
        wage_arm = random.choice(['A', 'B'])
        posting_order_seed = random.randint(1, 999999)

        # Random occupation pool
        occupation_pool = random.choice([
            'business_analyst', 'financial_analyst', 'marketing_analyst',
        ])

        participant = Participant(
            user_id=user_id,
            study_assignment=study,
            wage_arm=wage_arm,
            prolific_id=prolific_id,
            posting_order_seed=posting_order_seed,
            occupation_pool=occupation_pool,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        participant.save()

        request.session['participant_id'] = str(participant.id)
        request.session['session_start_time'] = time.time()
        return redirect('core:consent')


class ConsentView(SurveyFlowMixin, TemplateView):
    template_name = 'consent.html'
    requires_consent = False

    def post(self, request, *args, **kwargs):
        participant = self.get_participant()
        if not participant:
            return redirect('core:landing')

        if request.POST.get('consent') == 'agree':
            participant.consented = True
            participant.consent_timestamp = timezone.now()
            participant.status = 'consented'
            participant.save()
            # Route to the study-specific flow
            return redirect('core:read_postings')

        return redirect('core:withdraw')


# ---------------------------------------------------------------------------
# Posting reading (shared entry point for Study 2 & 3)
# ---------------------------------------------------------------------------

class ReadPostingsView(SurveyFlowMixin, TemplateView):
    template_name = 'read_postings.html'

    def get(self, request, *args, **kwargs):
        participant = self.get_participant()
        self.update_status(participant, 'reading')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        participant = self.get_participant()
        posting_ids = participant.get_posting_order()
        ctx['postings'] = [Posting.objects.get(id=pid) for pid in posting_ids]
        ctx['participant'] = participant
        return ctx

    def post(self, request, *args, **kwargs):
        participant = self.get_participant()
        # Both study paths go to rankings for now (Study 2)
        # Study 3/4 competition tasks will be added before this later
        return redirect('core:study2_ranking', dimension_num=1)


# ---------------------------------------------------------------------------
# Study 2: Ranking Task (7 dimensions)
# ---------------------------------------------------------------------------

RANKING_DIMENSIONS = [
    {
        'slug': 'perceived_pay',
        'prompt': 'Which of these employers do you think pays the most?',
        'anchor_high': 'highest',
        'anchor_low': 'lowest pay',
        'wages_always_hidden': True,
    },
    {
        'slug': 'mission_identity',
        'prompt': 'Which organization has the clearest mission or identity?',
        'anchor_high': 'highest',
        'anchor_low': 'least clear',
        'wages_always_hidden': False,
    },
    {
        'slug': 'belief_alignment',
        'prompt': "At which company would an employee's personal beliefs and goals "
                  "most influence their experience working there?",
        'anchor_high': 'highest',
        'anchor_low': 'least influence',
        'wages_always_hidden': False,
    },
    {
        'slug': 'employer_quality',
        'prompt': 'Which of these do you think would be a better employer?',
        'anchor_high': 'highest',
        'anchor_low': 'worst',
        'wages_always_hidden': False,
    },
    {
        'slug': 'overall_desirability',
        'prompt': 'Where would you most want to work?',
        'anchor_high': 'highest',
        'anchor_low': 'least desirable',
        'wages_always_hidden': False,
    },
]


class RankingInstructionsView(SurveyFlowMixin, TemplateView):
    template_name = 'study2/instructions.html'

    def get(self, request, *args, **kwargs):
        participant = self.get_participant()
        self.update_status(participant, 'stage1')
        return super().get(request, *args, **kwargs)


class RankingDimensionView(SurveyFlowMixin, TemplateView):
    template_name = 'study2/ranking.html'

    def get_dimension(self, dimension_num):
        idx = dimension_num - 1
        if 0 <= idx < len(RANKING_DIMENSIONS):
            return RANKING_DIMENSIONS[idx]
        return None

    def get_wage_display(self, participant, dimension):
        if dimension['wages_always_hidden']:
            return 'hidden'
        # Wages visible for everyone on all dimensions after perceived pay
        return 'visible'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        participant = self.get_participant()
        dimension_num = kwargs['dimension_num']
        dimension = self.get_dimension(dimension_num)

        posting_ids = participant.get_posting_order()
        postings = [Posting.objects.get(id=pid) for pid in posting_ids]

        wage_display = self.get_wage_display(participant, dimension)

        # After perceived_pay (dim 1), reorder by participant's pay ranking
        # and reveal wages that match their ranking (rank 1 = highest salary)
        pay_reveal = False
        if dimension_num == 2:
            pay_ranking = participant.get_pay_ranking()
            if pay_ranking:
                signal_to_posting = {p.signal_type: p for p in postings}
                reordered = [signal_to_posting[s] for s in pay_ranking
                             if s in signal_to_posting]
                if len(reordered) == len(postings):
                    postings = reordered
                pay_reveal = True
                wage_display = 'visible'

        # Annotate each posting with its salary text (None if no ranking yet)
        for posting in postings:
            posting.salary_text_for_participant = posting.get_salary_text(participant)

        ctx['postings'] = postings
        ctx['participant'] = participant
        ctx['dimension'] = dimension
        ctx['dimension_num'] = dimension_num
        ctx['total_dimensions'] = len(RANKING_DIMENSIONS)
        ctx['wage_display'] = wage_display
        ctx['pay_reveal'] = pay_reveal
        return ctx

    def post(self, request, *args, **kwargs):
        participant = self.get_participant()
        dimension_num = kwargs['dimension_num']
        dimension = self.get_dimension(dimension_num)

        ranking_order_str = request.POST.get('ranking_order', '')
        ranking_order = [x.strip() for x in ranking_order_str.split(',') if x.strip()]

        try:
            response_time = float(request.POST.get('response_time_seconds', 0))
        except (ValueError, TypeError):
            response_time = None

        RankingResponse.objects.update_or_create(
            participant=participant,
            dimension=dimension['slug'],
            defaults={
                'dimension_order': dimension_num,
                'ranking_order': ranking_order,
                'response_time_seconds': response_time,
            }
        )

        if dimension_num < len(RANKING_DIMENSIONS):
            return redirect('core:study2_ranking', dimension_num=dimension_num + 1)

        # Set card_sort_posting to the #1 ranked posting on overall desirability
        if ranking_order:
            top_signal = ranking_order[0]
            top_posting = Posting.objects.filter(
                occupation_pool=participant.occupation_pool,
                signal_type=top_signal,
            ).first()
            if top_posting:
                participant.card_sort_posting = top_posting
                participant.save(update_fields=['card_sort_posting'])

        # After all rankings, go to study-specific card sort transition
        if participant.study_assignment == 'study3':
            return redirect('core:hm_card_sort_transition')
        return redirect('core:card_sort_transition')


# ---------------------------------------------------------------------------
# Study 2: Card Sort & Competition (Stages 2-3)
# ---------------------------------------------------------------------------

class CardSortTransitionView(SurveyFlowMixin, TemplateView):
    template_name = 'study2/card_sort_transition.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        participant = self.get_participant()
        posting = participant.card_sort_posting
        if posting:
            posting.salary_text_for_participant = posting.get_salary_text(participant)
        ctx['participant'] = participant
        ctx['posting'] = posting
        ctx['wage_display'] = 'visible' if participant.wage_arm == 'A' else 'hidden'
        return ctx

    def post(self, request, *args, **kwargs):
        participant = self.get_participant()
        self.update_status(participant, 'stage2')
        return redirect('core:card_sort')


class CardSortView(SurveyFlowMixin, TemplateView):
    template_name = 'study2/card_sort.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        participant = self.get_participant()
        posting = participant.card_sort_posting

        if posting:
            posting.salary_text_for_participant = posting.get_salary_text(participant)

        # Randomize card order using participant seed
        cards = list(CardSortCard.objects.all())
        rng = random.Random(participant.posting_order_seed)
        rng.shuffle(cards)

        # Determine card color index (1-based position in posting order)
        card_num = 1
        if posting:
            posting_order = participant.get_posting_order()
            try:
                card_num = posting_order.index(posting.id) + 1
            except ValueError:
                pass

        ctx['participant'] = participant
        ctx['posting'] = posting
        ctx['cards'] = cards
        ctx['card_num'] = card_num
        ctx['wage_display'] = 'visible' if participant.wage_arm == 'A' else 'hidden'
        return ctx

    def post(self, request, *args, **kwargs):
        participant = self.get_participant()
        posting = participant.card_sort_posting

        cards_selected = request.POST.get('cards_selected', '')
        selection_order = request.POST.get('selection_order', '')
        response_time = request.POST.get('response_time_ms', '')

        cards_list = [c.strip() for c in cards_selected.split(',') if c.strip()]
        order_list = [c.strip() for c in selection_order.split(',') if c.strip()]

        try:
            response_time_ms = int(response_time) if response_time else None
        except ValueError:
            response_time_ms = None

        CardSortResponse.objects.update_or_create(
            participant=participant,
            stage='card_sort',
            defaults={
                'posting': posting,
                'cards_selected': cards_list,
                'selection_order': order_list,
                'response_time_ms': response_time_ms,
            }
        )

        return redirect('core:competition')


class CompetitionView(SurveyFlowMixin, TemplateView):
    template_name = 'study2/competition.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        participant = self.get_participant()
        posting = participant.card_sort_posting

        if posting:
            posting.salary_text_for_participant = posting.get_salary_text(participant)

        # Get original card sort selections
        original = CardSortResponse.objects.filter(
            participant=participant, stage='card_sort').first()
        original_card_ids = original.cards_selected if original else []

        # Load card objects for the original selection
        original_cards = []
        if original_card_ids:
            card_map = {c.card_id: c for c in CardSortCard.objects.all()}
            original_cards = [card_map[cid] for cid in original_card_ids if cid in card_map]

        # Randomize card order (different seed offset for competition)
        cards = list(CardSortCard.objects.all())
        rng = random.Random((participant.posting_order_seed or 0) + 7)
        rng.shuffle(cards)

        # Determine card color index (1-based position in posting order)
        card_num = 1
        if posting:
            posting_order = participant.get_posting_order()
            try:
                card_num = posting_order.index(posting.id) + 1
            except ValueError:
                pass

        ctx['participant'] = participant
        ctx['posting'] = posting
        ctx['cards'] = cards
        ctx['card_num'] = card_num
        ctx['original_cards'] = original_cards
        ctx['original_card_ids_json'] = json.dumps(original_card_ids)
        ctx['wage_display'] = 'visible' if participant.wage_arm == 'A' else 'hidden'
        return ctx

    def post(self, request, *args, **kwargs):
        participant = self.get_participant()
        posting = participant.card_sort_posting

        keep_original = request.POST.get('keep_original') == 'true'

        if keep_original:
            # Copy original selections
            original = CardSortResponse.objects.filter(
                participant=participant, stage='card_sort').first()
            cards_list = original.cards_selected if original else []
            order_list = original.selection_order if original else []
        else:
            cards_selected = request.POST.get('cards_selected', '')
            selection_order = request.POST.get('selection_order', '')
            cards_list = [c.strip() for c in cards_selected.split(',') if c.strip()]
            order_list = [c.strip() for c in selection_order.split(',') if c.strip()]

        response_time = request.POST.get('response_time_ms', '')
        try:
            response_time_ms = int(response_time) if response_time else None
        except ValueError:
            response_time_ms = None

        CardSortResponse.objects.update_or_create(
            participant=participant,
            stage='competition',
            defaults={
                'posting': posting,
                'cards_selected': cards_list,
                'selection_order': order_list,
                'keep_original': keep_original,
                'response_time_ms': response_time_ms,
            }
        )

        self.update_status(participant, 'stage3')
        return redirect('core:bucket_sort_transition')


# ---------------------------------------------------------------------------
# Study 3: Hiring Manager Card Sort & Competition
# ---------------------------------------------------------------------------

class HMCardSortTransitionView(SurveyFlowMixin, TemplateView):
    template_name = 'study3/card_sort_transition.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        participant = self.get_participant()
        posting = participant.card_sort_posting
        if posting:
            posting.salary_text_for_participant = posting.get_salary_text(participant)
        ctx['participant'] = participant
        ctx['posting'] = posting
        ctx['wage_display'] = 'visible' if participant.wage_arm == 'A' else 'hidden'
        return ctx

    def post(self, request, *args, **kwargs):
        participant = self.get_participant()
        self.update_status(participant, 'stage2')
        return redirect('core:hm_card_sort')


class HMCardSortView(SurveyFlowMixin, TemplateView):
    template_name = 'study3/card_sort.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        participant = self.get_participant()
        posting = participant.card_sort_posting

        if posting:
            posting.salary_text_for_participant = posting.get_salary_text(participant)

        cards = list(HiringManagerCard.objects.all())
        rng = random.Random(participant.posting_order_seed)
        rng.shuffle(cards)

        # Determine card color index (1-based position in posting order)
        card_num = 1
        if posting:
            posting_order = participant.get_posting_order()
            try:
                card_num = posting_order.index(posting.id) + 1
            except ValueError:
                pass

        ctx['participant'] = participant
        ctx['posting'] = posting
        ctx['cards'] = cards
        ctx['card_num'] = card_num
        ctx['wage_display'] = 'visible' if participant.wage_arm == 'A' else 'hidden'
        return ctx

    def post(self, request, *args, **kwargs):
        participant = self.get_participant()
        posting = participant.card_sort_posting

        cards_selected = request.POST.get('cards_selected', '')
        selection_order = request.POST.get('selection_order', '')
        response_time = request.POST.get('response_time_ms', '')

        cards_list = [c.strip() for c in cards_selected.split(',') if c.strip()]
        order_list = [c.strip() for c in selection_order.split(',') if c.strip()]

        try:
            response_time_ms = int(response_time) if response_time else None
        except ValueError:
            response_time_ms = None

        HiringManagerResponse.objects.update_or_create(
            participant=participant,
            stage='card_sort',
            defaults={
                'posting': posting,
                'cards_selected': cards_list,
                'selection_order': order_list,
                'response_time_ms': response_time_ms,
            }
        )

        return redirect('core:hm_competition')


class HMCompetitionView(SurveyFlowMixin, TemplateView):
    template_name = 'study3/competition.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        participant = self.get_participant()
        posting = participant.card_sort_posting

        if posting:
            posting.salary_text_for_participant = posting.get_salary_text(participant)

        # Get original card sort selections
        original = HiringManagerResponse.objects.filter(
            participant=participant, stage='card_sort').first()
        original_card_ids = original.cards_selected if original else []

        original_cards = []
        if original_card_ids:
            card_map = {c.card_id: c for c in HiringManagerCard.objects.all()}
            original_cards = [card_map[cid] for cid in original_card_ids if cid in card_map]

        # Randomize card order (different seed offset for competition)
        cards = list(HiringManagerCard.objects.all())
        rng = random.Random((participant.posting_order_seed or 0) + 7)
        rng.shuffle(cards)

        # Determine card color index (1-based position in posting order)
        card_num = 1
        if posting:
            posting_order = participant.get_posting_order()
            try:
                card_num = posting_order.index(posting.id) + 1
            except ValueError:
                pass

        ctx['participant'] = participant
        ctx['posting'] = posting
        ctx['cards'] = cards
        ctx['card_num'] = card_num
        ctx['original_cards'] = original_cards
        ctx['original_card_ids_json'] = json.dumps(original_card_ids)
        ctx['wage_display'] = 'visible' if participant.wage_arm == 'A' else 'hidden'
        return ctx

    def post(self, request, *args, **kwargs):
        participant = self.get_participant()
        posting = participant.card_sort_posting

        would_change = request.POST.get('would_change') == 'yes'

        cards_selected = request.POST.get('cards_selected', '')
        selection_order = request.POST.get('selection_order', '')
        cards_list = [c.strip() for c in cards_selected.split(',') if c.strip()]
        order_list = [c.strip() for c in selection_order.split(',') if c.strip()]

        response_time = request.POST.get('response_time_ms', '')
        try:
            response_time_ms = int(response_time) if response_time else None
        except ValueError:
            response_time_ms = None

        HiringManagerResponse.objects.update_or_create(
            participant=participant,
            stage='competition',
            defaults={
                'posting': posting,
                'cards_selected': cards_list,
                'selection_order': order_list,
                'would_change': would_change,
                'response_time_ms': response_time_ms,
            }
        )

        self.update_status(participant, 'stage3')
        return redirect('core:bucket_sort_transition')


# ---------------------------------------------------------------------------
# Demographics & Individual Differences
# ---------------------------------------------------------------------------

class IndividualDifferencesView(SurveyFlowMixin, TemplateView):
    template_name = 'individual_differences.html'

    def get(self, request, *args, **kwargs):
        participant = self.get_participant()
        self.update_status(participant, 'individual_diffs')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        participant = self.get_participant()
        P = request.POST

        def safe_int(key):
            val = P.get(key)
            try:
                return int(val) if val else None
            except ValueError:
                return None

        IndividualDifferences.objects.create(
            participant=participant,
            jsv_salary=safe_int('jsv_salary'),
            jsv_benefits=safe_int('jsv_benefits'),
            jsv_mission=safe_int('jsv_mission'),
            jsv_worklife=safe_int('jsv_worklife'),
            jsv_growth=safe_int('jsv_growth'),
            jsv_security=safe_int('jsv_security'),
            jsv_impact=safe_int('jsv_impact'),
            jsv_autonomy=safe_int('jsv_autonomy'),
            jsv_coworkers=safe_int('jsv_coworkers'),
            jsv_reputation=safe_int('jsv_reputation'),
            csr_responsibility=safe_int('csr_responsibility'),
            csr_lower_salary=safe_int('csr_lower_salary'),
            csr_usually_mean_it=safe_int('csr_usually_mean_it'),
            csr_pay_attention=safe_int('csr_pay_attention'),
            skep_improve_image=safe_int('skep_improve_image'),
            skep_grain_of_salt=safe_int('skep_grain_of_salt'),
            skep_genuinely_motivated=safe_int('skep_genuinely_motivated'),
            political_orientation=safe_int('political_orientation'),
            household_income=P.get('household_income', ''),
            job_search_urgency=safe_int('job_search_urgency'),
            job_satisfaction=safe_int('job_satisfaction'),
        )
        return redirect('core:demographics')


class DemographicsView(SurveyFlowMixin, TemplateView):
    template_name = 'demographics.html'

    def get(self, request, *args, **kwargs):
        participant = self.get_participant()
        self.update_status(participant, 'demographics')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        participant = self.get_participant()
        P = request.POST

        def safe_int(key):
            val = P.get(key)
            try:
                return int(val) if val else None
            except ValueError:
                return None

        Demographics.objects.create(
            participant=participant,
            age=safe_int('age'),
            gender=P.get('gender', ''),
            gender_other=P.get('gender_other', ''),
            race=P.get('race', ''),
            race_other=P.get('race_other', ''),
            parents_income=P.get('parents_income', ''),
            high_school_state=P.get('high_school_state', ''),
            neighborhood=P.get('neighborhood', ''),
            major=P.get('major', ''),
            major_other=P.get('major_other', ''),
            year_in_program=P.get('year_in_program', ''),
            has_part_time_job=P.get('has_part_time_job', ''),
            english_first_language=P.get('english_first_language', ''),
            first_language=P.get('first_language', ''),
        )

        participant.status = 'completed'
        participant.completed_at = timezone.now()
        participant.save()
        return redirect('core:debrief')


# ---------------------------------------------------------------------------
# Study 1: Bucket Sort Game
# ---------------------------------------------------------------------------

BUCKET_LABELS = {
    'purpose': 'Organizational Purpose',
    'good_employer': 'Good Employer',
    'compensation': 'Compensation & Benefits',
    'job_tasks': 'Job Tasks & Requirements',
    'not_sure': 'Not Sure',
}


class BucketSortTransitionView(SurveyFlowMixin, TemplateView):
    template_name = 'study1/transition.html'

    def get(self, request, *args, **kwargs):
        participant = self.get_participant()
        self.update_status(participant, 'stage4')
        return super().get(request, *args, **kwargs)


class BucketSortInstructionsView(SurveyFlowMixin, TemplateView):
    template_name = 'study1/instructions.html'


class BucketSortGameView(SurveyFlowMixin, TemplateView):
    template_name = 'study1/game.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        participant = self.get_participant()

        phrases = list(
            BucketSortPhrase.objects.filter(is_active=True)
            .values('phrase_id', 'phrase_text', 'difficulty', 'expected_bucket'))

        seed = participant.posting_order_seed or random.randint(1, 999999)

        # Dynamic game duration: fit within 19-minute session, reserve 2 min for demographics + end
        session_start = self.request.session.get('session_start_time')
        if session_start:
            elapsed = time.time() - session_start
            game_duration = min(240, max(60, (19 * 60) - elapsed - 120))
        else:
            game_duration = 240  # fallback: 4 minutes

        ctx['phrases_json'] = json.dumps(phrases)
        ctx['seed'] = seed
        ctx['game_duration'] = int(game_duration)
        return ctx


class BucketSortSubmitView(SurveyFlowMixin, View):
    """AJAX endpoint that receives all game results as JSON."""

    def post(self, request, *args, **kwargs):
        participant = self.get_participant()
        if not participant:
            return JsonResponse({'error': 'No participant'}, status=400)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        results = data.get('results', [])
        inconsistent = data.get('inconsistent', [])

        # Build phrase lookup
        phrase_map = {}
        for p in BucketSortPhrase.objects.all():
            phrase_map[p.phrase_id] = p

        # Save all responses
        response_objects = []
        for r in results:
            phrase = phrase_map.get(r.get('phraseId'))
            if not phrase:
                continue
            response_objects.append(BucketSortResponse(
                participant=participant,
                phrase=phrase,
                attempt=r.get('attempt', 1),
                bucket_assigned=r.get('bucket', ''),
                was_missed=r.get('wasMissed', False),
                time_on_phrase_ms=r.get('timeOnPhraseMs'),
                game_elapsed_ms=r.get('gameElapsedMs'),
            ))
        BucketSortResponse.objects.bulk_create(response_objects)

        # Store inconsistent phrases in session for reconciliation
        if inconsistent:
            request.session['inconsistent_phrases'] = inconsistent
            redirect_url = '/study1/reconciliation/'
        else:
            redirect_url = '/demographics/'

        return JsonResponse({'redirect': redirect_url})


class BucketSortReconciliationView(SurveyFlowMixin, TemplateView):
    template_name = 'study1/reconciliation.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        inconsistent = self.request.session.get('inconsistent_phrases', [])

        # Enrich with labels
        for item in inconsistent:
            buckets = item.get('buckets', [])
            item['first_label'] = BUCKET_LABELS.get(buckets[0], buckets[0]) if len(buckets) > 0 else ''
            item['second_label'] = BUCKET_LABELS.get(buckets[1], buckets[1]) if len(buckets) > 1 else ''
            item['phrase_id'] = item.get('phraseId', '')
            item['phrase_text'] = item.get('phraseText', '')

        ctx['inconsistent_phrases'] = inconsistent
        ctx['buckets'] = list(BUCKET_LABELS.items())
        return ctx

    def post(self, request, *args, **kwargs):
        participant = self.get_participant()
        inconsistent = request.session.get('inconsistent_phrases', [])

        phrase_map = {}
        for p in BucketSortPhrase.objects.all():
            phrase_map[p.phrase_id] = p

        for item in inconsistent:
            phrase_id = item.get('phraseId', '')
            phrase = phrase_map.get(phrase_id)
            if not phrase:
                continue

            resolution = request.POST.get(f'resolve_{phrase_id}', '')
            final_bucket = request.POST.get(f'final_{phrase_id}', '')
            buckets = item.get('buckets', [])

            BucketSortReconciliation.objects.update_or_create(
                participant=participant,
                phrase=phrase,
                defaults={
                    'first_bucket': buckets[0] if len(buckets) > 0 else '',
                    'second_bucket': buckets[1] if len(buckets) > 1 else '',
                    'resolution': resolution,
                    'final_bucket': final_bucket if resolution == 'mistake' else '',
                })

        # Clean up session
        request.session.pop('inconsistent_phrases', None)
        return redirect('core:demographics')


# ---------------------------------------------------------------------------
# Debrief & Withdrawal
# ---------------------------------------------------------------------------

class DebriefView(SurveyFlowMixin, TemplateView):
    template_name = 'debrief.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        participant = self.get_participant()
        if participant:
            ctx['study_assignment'] = participant.study_assignment
            ctx['participant_code'] = participant.participant_code
            ctx['completion_code'] = participant.completion_code
        return ctx


class WithdrawView(SurveyFlowMixin, TemplateView):
    template_name = 'withdrawn.html'
    requires_consent = False

    def get(self, request, *args, **kwargs):
        participant = self.get_participant()
        if participant:
            self.update_status(participant, 'withdrawn')
        return super().get(request, *args, **kwargs)
