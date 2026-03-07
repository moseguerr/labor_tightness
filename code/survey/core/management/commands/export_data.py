"""
Export survey response data as CSV files.

Usage:
    python manage.py export_data                     # Exports to stdout summary
    python manage.py export_data --outdir ./exports  # Exports CSVs to directory
"""
import csv
import os
from io import StringIO

from django.core.management.base import BaseCommand
from django.db.models import F

from core.models import (
    Participant, Study1Response, Study1PostTask,
    PostingViewRecord, Study2ManipulationCheck,
    Study2Ranking, Study2PostRanking, Demographics,
)


class Command(BaseCommand):
    help = 'Export all response data as CSV files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--outdir', type=str, default='',
            help='Directory to write CSV files (default: print summary to stdout)')

    def handle(self, *args, **options):
        outdir = options['outdir']
        if outdir:
            os.makedirs(outdir, exist_ok=True)

        self._export_participants(outdir)
        self._export_study1_responses(outdir)
        self._export_study1_post_task(outdir)
        self._export_posting_views(outdir)
        self._export_manipulation_checks(outdir)
        self._export_rankings(outdir)
        self._export_post_ranking(outdir)
        self._export_demographics(outdir)

        if outdir:
            self.stdout.write(self.style.SUCCESS(f'All CSVs exported to {outdir}/'))
        else:
            self.stdout.write(self.style.SUCCESS('Summary complete. Use --outdir to write CSVs.'))

    def _write_csv(self, filename, headers, rows, outdir):
        if outdir:
            path = os.path.join(outdir, filename)
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
            self.stdout.write(f'  {filename}: {len(rows)} rows')
        else:
            self.stdout.write(f'  {filename}: {len(rows)} rows (use --outdir to save)')

    def _export_participants(self, outdir):
        headers = [
            'participant_code', 'session_type', 'status',
            'consented', 'started_at', 'completed_at',
            'duration_seconds', 'phrase_seed', 'posting_order_seed',
            'attention_passed', 'attention_failed', 'flagged',
            'external_id',
        ]
        rows = []
        for p in Participant.objects.all():
            rows.append([
                p.participant_code, p.session_type, p.status,
                p.consented, p.started_at, p.completed_at,
                p.duration_seconds, p.phrase_seed, p.posting_order_seed,
                p.attention_checks_passed, p.attention_checks_failed,
                p.flagged_for_exclusion, p.external_id,
            ])
        self._write_csv('participants.csv', headers, rows, outdir)

    def _export_study1_responses(self, outdir):
        headers = [
            'participant_code', 'phrase_text', 'phrase_type', 'irb_category',
            'presentation_order', 'mission_values', 'treats_well',
            'pay_benefits', 'job_tasks', 'job_requirements', 'none_unsure',
            'is_correct', 'displayed_at', 'responded_at', 'time_spent_seconds',
        ]
        rows = []
        for r in Study1Response.objects.select_related('participant', 'phrase').all():
            rows.append([
                r.participant.participant_code,
                r.phrase.phrase_text[:80],
                r.phrase.item_type,
                r.phrase.irb_category,
                r.presentation_order,
                int(r.selected_mission_values),
                int(r.selected_treats_well),
                int(r.selected_pay_benefits),
                int(r.selected_job_tasks),
                int(r.selected_job_requirements),
                int(r.selected_none_unsure),
                r.is_correct,
                r.displayed_at,
                r.responded_at,
                r.time_spent_seconds,
            ])
        self._write_csv('study1_responses.csv', headers, rows, outdir)

    def _export_study1_post_task(self, outdir):
        headers = ['participant_code', 'confidence', 'confusion_text', 'familiarity']
        rows = []
        for pt in Study1PostTask.objects.select_related('participant').all():
            rows.append([
                pt.participant.participant_code,
                pt.confidence, pt.confusion_text, pt.familiarity,
            ])
        self._write_csv('study1_post_task.csv', headers, rows, outdir)

    def _export_posting_views(self, outdir):
        headers = [
            'participant_code', 'company_name', 'condition_label',
            'presentation_order', 'viewed_at', 'time_spent_seconds',
        ]
        rows = []
        for pv in PostingViewRecord.objects.select_related('participant', 'posting').all():
            rows.append([
                pv.participant.participant_code,
                pv.posting.company_name,
                pv.posting.condition_label,
                pv.presentation_order,
                pv.viewed_at,
                pv.time_spent_seconds,
            ])
        self._write_csv('study2_posting_views.csv', headers, rows, outdir)

    def _export_manipulation_checks(self, outdir):
        headers = [
            'participant_code', 'most_mission', 'most_workplace',
            'highest_salary', 'job_title_check',
        ]
        rows = []
        for mc in Study2ManipulationCheck.objects.select_related('participant').all():
            rows.append([
                mc.participant.participant_code,
                mc.most_mission, mc.most_workplace,
                mc.highest_salary, mc.job_title_check,
            ])
        self._write_csv('study2_manipulation_checks.csv', headers, rows, outdir)

    def _export_rankings(self, outdir):
        headers = ['participant_code', 'dimension', 'rank_1', 'rank_2', 'rank_3',
                    'rank_4', 'rank_5', 'rank_6']
        rows = []
        for r in Study2Ranking.objects.select_related('participant').all():
            order = r.ranking_order or []
            padded = order + [''] * (6 - len(order))
            rows.append([
                r.participant.participant_code, r.dimension,
                *padded[:6],
            ])
        self._write_csv('study2_rankings.csv', headers, rows, outdir)

    def _export_post_ranking(self, outdir):
        headers = [
            'participant_code', 'top_company', 'explanation_text',
            'min_acceptable_salary', 'po_fit_values', 'po_fit_belong', 'po_fit_care',
        ]
        rows = []
        for pr in Study2PostRanking.objects.select_related('participant').all():
            rows.append([
                pr.participant.participant_code, pr.top_company,
                pr.explanation_text, pr.min_acceptable_salary,
                pr.po_fit_values, pr.po_fit_belong, pr.po_fit_care,
            ])
        self._write_csv('study2_post_ranking.csv', headers, rows, outdir)

    def _export_demographics(self, outdir):
        headers = [
            'participant_code', 'age', 'gender', 'gender_self_describe',
            'education', 'employment_status', 'employment_other',
            'industry', 'industry_other', 'work_experience_years', 'last_job_search',
        ]
        rows = []
        for d in Demographics.objects.select_related('participant').all():
            rows.append([
                d.participant.participant_code, d.age, d.gender, d.gender_self_describe,
                d.education, d.employment_status, d.employment_other,
                d.industry, d.industry_other, d.work_experience_years, d.last_job_search,
            ])
        self._write_csv('demographics.csv', headers, rows, outdir)
