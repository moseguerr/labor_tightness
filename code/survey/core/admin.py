from django.contrib import admin
from .models import (
    Participant, Phrase, Study1Response, Study1PostTask,
    JobPosting, PostingViewRecord, Study2ManipulationCheck,
    Study2Ranking, Study2PostRanking, IndividualDifferences, Demographics,
)


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = [
        'participant_code', 'session_type', 'status',
        'started_at', 'completed_at', 'flagged_for_exclusion',
    ]
    list_filter = ['session_type', 'status', 'flagged_for_exclusion']
    search_fields = ['participant_code', 'external_id']
    readonly_fields = ['id', 'started_at']


@admin.register(Phrase)
class PhraseAdmin(admin.ModelAdmin):
    list_display = ['phrase_text_short', 'item_type', 'irb_category', 'is_active']
    list_filter = ['item_type', 'irb_category', 'is_active']

    def phrase_text_short(self, obj):
        return obj.phrase_text[:60]
    phrase_text_short.short_description = 'Phrase'


@admin.register(Study1Response)
class Study1ResponseAdmin(admin.ModelAdmin):
    list_display = [
        'participant', 'phrase', 'presentation_order', 'is_correct',
    ]
    list_filter = ['is_correct']
    raw_id_fields = ['participant', 'phrase']


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ['condition_label', 'company_name', 'framing', 'salary_level', 'salary_amount']
    list_filter = ['framing', 'salary_level']


@admin.register(Study2Ranking)
class Study2RankingAdmin(admin.ModelAdmin):
    list_display = ['participant', 'dimension']
    list_filter = ['dimension']
    raw_id_fields = ['participant']


# Simple registrations for the rest
admin.site.register(Study1PostTask)
admin.site.register(PostingViewRecord)
admin.site.register(Study2ManipulationCheck)
admin.site.register(Study2PostRanking)
admin.site.register(IndividualDifferences)
admin.site.register(Demographics)
