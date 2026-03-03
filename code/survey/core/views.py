import random
from django.shortcuts import redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView, FormView
from django.utils import timezone
from django.http import HttpResponse

from .models import (
    Participant, Phrase, Study1Response, Study1PostTask,
    JobPosting, PostingViewRecord, Study2ManipulationCheck,
    Study2Ranking, Study2PostRanking, IndividualDifferences, Demographics,
)


# ---------------------------------------------------------------------------
# Flow control mixin
# ---------------------------------------------------------------------------

class SurveyFlowMixin:
    """
    Mixin that manages participant session state and enforces linear flow.
    """
    step_name = None

    def get_participant(self):
        participant_id = self.request.session.get('participant_id')
        if not participant_id:
            return None
        try:
            return Participant.objects.get(id=participant_id)
        except Participant.DoesNotExist:
            return None

    def dispatch(self, request, *args, **kwargs):
        participant = self.get_participant()
        # Landing and consent don't require a participant yet
        if self.step_name in ('landing', 'consent', 'withdraw'):
            return super().dispatch(request, *args, **kwargs)
        if not participant:
            return redirect('core:landing')
        if not participant.consented:
            return redirect('core:consent')
        return super().dispatch(request, *args, **kwargs)


# ---------------------------------------------------------------------------
# Entry flow
# ---------------------------------------------------------------------------

class LandingView(SurveyFlowMixin, TemplateView):
    template_name = 'landing.html'
    step_name = 'landing'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Pre-select session type from URL param if provided
        ctx['preselected'] = self.request.GET.get('session_type', '')
        return ctx

    def post(self, request, *args, **kwargs):
        session_type = request.POST.get('session_type')
        if session_type not in ('study1', 'study2', 'combined'):
            return self.get(request, *args, **kwargs)

        external_id = request.GET.get('external_id', '')

        participant = Participant(
            session_type=session_type,
            external_id=external_id,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        participant.save()

        request.session['participant_id'] = str(participant.id)
        return redirect('core:consent')


class ConsentView(SurveyFlowMixin, TemplateView):
    template_name = 'consent.html'
    step_name = 'consent'

    def post(self, request, *args, **kwargs):
        participant = self.get_participant()
        if not participant:
            return redirect('core:landing')

        if request.POST.get('consent') == 'agree':
            participant.consented = True
            participant.consent_timestamp = timezone.now()
            participant.save()

            if participant.session_type in ('study1', 'combined'):
                return redirect('core:study1_instructions')
            else:
                return redirect('core:study2_instructions')

        # Did not consent — withdraw
        return redirect('core:withdraw')


# ---------------------------------------------------------------------------
# Study 1
# ---------------------------------------------------------------------------

class Study1InstructionsView(SurveyFlowMixin, TemplateView):
    template_name = 'study1/instructions.html'
    step_name = 'study1_instructions'

    def get(self, request, *args, **kwargs):
        participant = self.get_participant()
        if participant and 'phrase_sequence' not in request.session:
            self._init_phrase_sequence(participant, request)
        participant.status = 'in_study1'
        participant.save()
        return super().get(request, *args, **kwargs)

    def _init_phrase_sequence(self, participant, request):
        """Build the phrase sequence: practice + shuffled main + interspersed attention."""
        seed = random.randint(1, 999999)
        participant.phrase_seed = seed
        participant.save()
        rng = random.Random(seed)

        practice_ids = list(
            Phrase.objects.filter(item_type='practice', is_active=True)
            .order_by('display_order').values_list('id', flat=True))
        attention_ids = list(
            Phrase.objects.filter(item_type='attention', is_active=True)
            .order_by('display_order').values_list('id', flat=True))
        main_ids = list(
            Phrase.objects.filter(item_type='main', is_active=True)
            .values_list('id', flat=True))

        # Sample 40 main items from pool
        sample_size = min(40, len(main_ids))
        sampled = rng.sample(main_ids, sample_size)
        rng.shuffle(sampled)

        # Intersperse attention checks at roughly even intervals
        sequence = list(practice_ids)  # practice first (fixed order)
        chunk_size = max(1, len(sampled) // (len(attention_ids) + 1))
        attn_idx = 0
        for i, phrase_id in enumerate(sampled):
            sequence.append(phrase_id)
            if (i + 1) % chunk_size == 0 and attn_idx < len(attention_ids):
                sequence.append(attention_ids[attn_idx])
                attn_idx += 1
        # Append remaining attention checks
        while attn_idx < len(attention_ids):
            sequence.append(attention_ids[attn_idx])
            attn_idx += 1

        request.session['phrase_sequence'] = sequence
        request.session['current_study1_item'] = 0


CATEGORY_CHOICES = [
    ('mission_values', "The company's mission, values, or social/environmental impact"),
    ('treats_well', 'The company treats employees well'),
    ('pay_benefits', 'Pay, benefits, or financial perks'),
    ('job_tasks', 'Job tasks, duties, or responsibilities'),
    ('job_requirements', 'Job requirements or qualifications'),
]


class Study1PracticeView(SurveyFlowMixin, TemplateView):
    template_name = 'study1/practice.html'
    step_name = 'study1_practice'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = CATEGORY_CHOICES
        item_num = self.kwargs['item_num']
        sequence = self.request.session.get('phrase_sequence', [])
        if item_num < len(sequence):
            phrase = Phrase.objects.get(id=sequence[item_num])
            ctx['phrase'] = phrase
            ctx['item_num'] = item_num
            ctx['total_items'] = len(sequence)
            ctx['is_practice'] = phrase.item_type == 'practice'
        return ctx

    def post(self, request, *args, **kwargs):
        item_num = self.kwargs['item_num']
        sequence = request.session.get('phrase_sequence', [])
        participant = self.get_participant()

        if item_num < len(sequence):
            phrase = Phrase.objects.get(id=sequence[item_num])

            # Save response
            response, _ = Study1Response.objects.get_or_create(
                participant=participant, phrase=phrase,
                defaults={'presentation_order': item_num + 1})
            response.selected_mission_values = 'mission_values' in request.POST.getlist('categories')
            response.selected_treats_well = 'treats_well' in request.POST.getlist('categories')
            response.selected_pay_benefits = 'pay_benefits' in request.POST.getlist('categories')
            response.selected_job_tasks = 'job_tasks' in request.POST.getlist('categories')
            response.selected_job_requirements = 'job_requirements' in request.POST.getlist('categories')
            response.selected_none_unsure = 'none_unsure' in request.POST.getlist('categories')
            response.responded_at = timezone.now()

            # Check correctness for attention checks
            if phrase.item_type == 'attention':
                correct_set = set(phrase.correct_categories)
                selected_set = set(response.selected_categories)
                response.is_correct = (correct_set == selected_set)
                if response.is_correct:
                    participant.attention_checks_passed += 1
                else:
                    participant.attention_checks_failed += 1
                if participant.attention_checks_failed >= 2:
                    participant.flagged_for_exclusion = True
                participant.save()

            response.save()

        # Determine next item
        next_num = item_num + 1
        request.session['current_study1_item'] = next_num

        if next_num >= len(sequence):
            return redirect('core:study1_post_task')

        next_phrase = Phrase.objects.get(id=sequence[next_num])
        if next_phrase.item_type == 'practice':
            return redirect('core:study1_practice', item_num=next_num)

        # Show feedback for practice items before advancing
        if item_num < len(sequence):
            current_phrase = Phrase.objects.get(id=sequence[item_num])
            if current_phrase.item_type == 'practice' and 'feedback_shown' not in request.POST:
                # Re-render with feedback
                return self.render_to_response(self.get_context_data(
                    show_feedback=True, item_num=item_num))

        return redirect('core:study1_classify', item_num=next_num)


class Study1ClassifyView(SurveyFlowMixin, TemplateView):
    template_name = 'study1/classify.html'
    step_name = 'study1_classify'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        item_num = self.kwargs['item_num']
        sequence = self.request.session.get('phrase_sequence', [])
        practice_count = Phrase.objects.filter(item_type='practice', is_active=True).count()

        if item_num < len(sequence):
            phrase = Phrase.objects.get(id=sequence[item_num])
            ctx['phrase'] = phrase
            ctx['item_num'] = item_num
            ctx['display_num'] = item_num - practice_count + 1  # Don't count practice in display
            ctx['total_classify'] = len(sequence) - practice_count
            ctx['total_items'] = len(sequence)
            ctx['progress_pct'] = int((item_num / len(sequence)) * 100)
        return ctx

    def post(self, request, *args, **kwargs):
        item_num = self.kwargs['item_num']
        sequence = request.session.get('phrase_sequence', [])
        participant = self.get_participant()

        if item_num < len(sequence):
            phrase = Phrase.objects.get(id=sequence[item_num])
            categories = request.POST.getlist('categories')

            response, _ = Study1Response.objects.get_or_create(
                participant=participant, phrase=phrase,
                defaults={'presentation_order': item_num + 1})
            response.selected_mission_values = 'mission_values' in categories
            response.selected_treats_well = 'treats_well' in categories
            response.selected_pay_benefits = 'pay_benefits' in categories
            response.selected_job_tasks = 'job_tasks' in categories
            response.selected_job_requirements = 'job_requirements' in categories
            response.selected_none_unsure = 'none_unsure' in categories
            response.responded_at = timezone.now()

            if phrase.item_type == 'attention':
                correct_set = set(phrase.correct_categories)
                selected_set = set(response.selected_categories)
                response.is_correct = (correct_set == selected_set)
                if response.is_correct:
                    participant.attention_checks_passed += 1
                else:
                    participant.attention_checks_failed += 1
                if participant.attention_checks_failed >= 2:
                    participant.flagged_for_exclusion = True
                participant.save()

            response.save()

        next_num = item_num + 1
        request.session['current_study1_item'] = next_num

        if next_num >= len(sequence):
            return redirect('core:study1_post_task')
        return redirect('core:study1_classify', item_num=next_num)


class Study1PostTaskView(SurveyFlowMixin, TemplateView):
    template_name = 'study1/post_task.html'
    step_name = 'study1_post_task'

    def post(self, request, *args, **kwargs):
        participant = self.get_participant()
        Study1PostTask.objects.create(
            participant=participant,
            confidence=int(request.POST.get('confidence', 4)),
            confusion_text=request.POST.get('confusion_text', ''),
            familiarity=int(request.POST.get('familiarity', 4)),
        )
        if participant.session_type == 'combined':
            return redirect('core:transition')
        return redirect('core:demographics')


# ---------------------------------------------------------------------------
# Transition (combined session)
# ---------------------------------------------------------------------------

class TransitionView(SurveyFlowMixin, TemplateView):
    template_name = 'transition.html'
    step_name = 'transition'


# ---------------------------------------------------------------------------
# Study 2
# ---------------------------------------------------------------------------

class Study2InstructionsView(SurveyFlowMixin, TemplateView):
    template_name = 'study2/instructions.html'
    step_name = 'study2_instructions'

    def get(self, request, *args, **kwargs):
        participant = self.get_participant()
        if participant and 'posting_sequence' not in request.session:
            self._init_posting_sequence(participant, request)
        participant.status = 'in_study2'
        participant.save()
        return super().get(request, *args, **kwargs)

    def _init_posting_sequence(self, participant, request):
        seed = random.randint(1, 999999)
        participant.posting_order_seed = seed
        participant.save()
        rng = random.Random(seed)

        posting_ids = list(
            JobPosting.objects.values_list('id', flat=True))
        rng.shuffle(posting_ids)

        request.session['posting_sequence'] = posting_ids
        request.session['current_posting'] = 0


class Study2PostingPageView(SurveyFlowMixin, TemplateView):
    template_name = 'study2/posting.html'
    step_name = 'study2_posting'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        posting_num = self.kwargs['posting_num']
        sequence = self.request.session.get('posting_sequence', [])

        if posting_num < len(sequence):
            posting = JobPosting.objects.get(id=sequence[posting_num])
            ctx['posting'] = posting
            ctx['posting_num'] = posting_num
            ctx['total_postings'] = len(sequence)
            ctx['progress_pct'] = int(((posting_num + 1) / len(sequence)) * 100)
        return ctx

    def post(self, request, *args, **kwargs):
        posting_num = self.kwargs['posting_num']
        sequence = request.session.get('posting_sequence', [])
        participant = self.get_participant()

        if posting_num < len(sequence):
            posting = JobPosting.objects.get(id=sequence[posting_num])
            PostingViewRecord.objects.get_or_create(
                participant=participant, posting=posting,
                defaults={
                    'presentation_order': posting_num + 1,
                    'viewed_at': timezone.now(),
                })

        next_num = posting_num + 1
        request.session['current_posting'] = next_num

        if next_num >= len(sequence):
            return redirect('core:manipulation_checks')
        return redirect('core:study2_posting', posting_num=next_num)


class ManipulationChecksView(SurveyFlowMixin, TemplateView):
    template_name = 'study2/manipulation_checks.html'
    step_name = 'manipulation_checks'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['companies'] = list(
            JobPosting.objects.values_list('company_name', flat=True))
        return ctx

    def post(self, request, *args, **kwargs):
        participant = self.get_participant()
        Study2ManipulationCheck.objects.create(
            participant=participant,
            most_mission=request.POST.get('most_mission', ''),
            most_workplace=request.POST.get('most_workplace', ''),
            highest_salary=request.POST.get('highest_salary', ''),
            job_title_check=request.POST.get('job_title_check', ''),
        )
        return redirect('core:post_ranking')


RANKING_DIMENSIONS = [
    'attractiveness', 'sincerity', 'employee_treatment',
    'accept_lower_pay', 'instrumentality',
]

RANKING_PROMPTS = {
    'attractiveness': 'Rank these job postings from the one you would most want to apply to (1) to the one you would least want to apply to (6).',
    'sincerity': 'Rank these companies from the one that seems most sincere about what it says in the posting (1) to the one that seems least sincere (6).',
    'employee_treatment': 'Rank these companies from the one you think treats its employees the best (1) to the one you think treats its employees the worst (6).',
    'accept_lower_pay': 'If you had to choose, which job would you be willing to accept the lowest salary for? Rank from the job you would accept the lowest salary for (1) to the job you would need the highest salary to accept (6).',
    'instrumentality': 'Which company seems to be using its stated values or workplace claims mainly as a recruitment tool, rather than a genuine commitment? Rank from the one that seems most like a recruitment tool (1) to the one that seems most genuine (6).',
}


class Study2RankingView(SurveyFlowMixin, TemplateView):
    template_name = 'study2/ranking.html'
    step_name = 'study2_ranking'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        dimension = self.kwargs['dimension']
        sequence = self.request.session.get('posting_sequence', [])

        ctx['dimension'] = dimension
        ctx['prompt'] = RANKING_PROMPTS.get(dimension, '')
        ctx['dimension_num'] = RANKING_DIMENSIONS.index(dimension) + 1
        ctx['total_dimensions'] = len(RANKING_DIMENSIONS)

        # Get full posting objects in the order participant saw them
        postings = []
        for pid in sequence:
            postings.append(JobPosting.objects.get(id=pid))
        ctx['postings'] = postings
        ctx['companies'] = [p.company_name for p in postings]
        return ctx

    def post(self, request, *args, **kwargs):
        participant = self.get_participant()
        dimension = self.kwargs['dimension']

        # ranking_order comes as comma-separated company names
        ranking_str = request.POST.get('ranking_order', '')
        ranking_order = [name.strip() for name in ranking_str.split(',') if name.strip()]

        Study2Ranking.objects.update_or_create(
            participant=participant, dimension=dimension,
            defaults={'ranking_order': ranking_order})

        # Next dimension
        current_idx = RANKING_DIMENSIONS.index(dimension)
        if current_idx + 1 < len(RANKING_DIMENSIONS):
            next_dim = RANKING_DIMENSIONS[current_idx + 1]
            return redirect('core:study2_ranking', dimension=next_dim)
        return redirect('core:manipulation_checks')


class PostRankingView(SurveyFlowMixin, TemplateView):
    template_name = 'study2/post_ranking.html'
    step_name = 'post_ranking'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        participant = self.get_participant()
        # Get top-ranked company from attractiveness dimension
        try:
            ranking = Study2Ranking.objects.get(
                participant=participant, dimension='attractiveness')
            ctx['top_company'] = ranking.ranking_order[0] if ranking.ranking_order else ''
        except Study2Ranking.DoesNotExist:
            ctx['top_company'] = ''
        return ctx

    def post(self, request, *args, **kwargs):
        participant = self.get_participant()
        top_company = request.POST.get('top_company', '')

        min_salary = request.POST.get('min_acceptable_salary')
        try:
            min_salary = int(min_salary) if min_salary else None
        except ValueError:
            min_salary = None

        Study2PostRanking.objects.create(
            participant=participant,
            top_company=top_company,
            explanation_text=request.POST.get('explanation_text', ''),
            min_acceptable_salary=min_salary,
            po_fit_values=int(request.POST.get('po_fit_values', 0)) or None,
            po_fit_belong=int(request.POST.get('po_fit_belong', 0)) or None,
            po_fit_care=int(request.POST.get('po_fit_care', 0)) or None,
        )
        return redirect('core:individual_differences')


class IndividualDifferencesView(SurveyFlowMixin, TemplateView):
    template_name = 'study2/individual_differences.html'
    step_name = 'individual_differences'

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


# ---------------------------------------------------------------------------
# Demographics & Debrief
# ---------------------------------------------------------------------------

class DemographicsView(SurveyFlowMixin, TemplateView):
    template_name = 'demographics.html'
    step_name = 'demographics'

    def get(self, request, *args, **kwargs):
        participant = self.get_participant()
        if participant:
            participant.status = 'in_demographics'
            participant.save()
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
            gender_self_describe=P.get('gender_self_describe', ''),
            education=P.get('education', ''),
            employment_status=P.get('employment_status', ''),
            employment_other=P.get('employment_other', ''),
            industry=P.get('industry', ''),
            industry_other=P.get('industry_other', ''),
            work_experience_years=safe_int('work_experience_years'),
            last_job_search=P.get('last_job_search', ''),
        )

        participant.status = 'completed'
        participant.completed_at = timezone.now()
        participant.save()
        return redirect('core:debrief')


class DebriefView(SurveyFlowMixin, TemplateView):
    template_name = 'debrief.html'
    step_name = 'debrief'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        participant = self.get_participant()
        if participant:
            ctx['session_type'] = participant.session_type
            ctx['participant_code'] = participant.participant_code
        return ctx


class WithdrawView(SurveyFlowMixin, TemplateView):
    template_name = 'withdrawn.html'
    step_name = 'withdraw'

    def get(self, request, *args, **kwargs):
        participant = self.get_participant()
        if participant:
            participant.status = 'withdrawn'
            participant.save()
        return super().get(request, *args, **kwargs)


# ---------------------------------------------------------------------------
# Researcher dashboard (staff only)
# ---------------------------------------------------------------------------

class DashboardView(TemplateView):
    template_name = 'dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect('core:landing')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from django.db.models import Avg, Count

        participants = Participant.objects.all()
        total = participants.count()
        completed = participants.filter(status='completed').count()
        in_progress = participants.exclude(
            status__in=('completed', 'withdrawn')).count()
        flagged = participants.filter(flagged_for_exclusion=True).count()

        ctx['total_participants'] = total
        ctx['completed_count'] = completed
        ctx['in_progress_count'] = in_progress
        ctx['flagged_count'] = flagged
        ctx['completion_rate'] = round(completed / total * 100) if total else 0

        type_counts = (participants.values('session_type')
                       .annotate(count=Count('id')).order_by('session_type'))
        ctx['session_type_counts'] = [
            (dict(Participant.SESSION_TYPES).get(tc['session_type'], tc['session_type']),
             tc['count']) for tc in type_counts]

        agg = participants.aggregate(
            avg_passed=Avg('attention_checks_passed'),
            avg_failed=Avg('attention_checks_failed'))
        ctx['avg_attention_passed'] = round(agg['avg_passed'] or 0, 1)
        ctx['avg_attention_failed'] = round(agg['avg_failed'] or 0, 1)
        ctx['exclusion_rate'] = round(flagged / total * 100) if total else 0
        ctx['recent_participants'] = participants[:20]

        return ctx


class ExportDataView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect('core:landing')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, fmt='csv'):
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'participant_code', 'session_type', 'status',
            'started_at', 'completed_at', 'flagged_for_exclusion'])
        for p in Participant.objects.all():
            writer.writerow([
                p.participant_code, p.session_type, p.status,
                p.started_at, p.completed_at, p.flagged_for_exclusion])

        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="participants.csv"'
        return response
