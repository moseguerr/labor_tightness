from django.contrib import admin
from .models import (
    Participant, Posting, Demographics, IndividualDifferences,
    RankingResponse, CardSortCard, CardSortResponse,
    HiringManagerCard, HiringManagerResponse,
    BucketSortPhrase, BucketSortResponse, BucketSortReconciliation,
)


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = [
        'participant_code', 'study_assignment', 'wage_arm', 'occupation_pool',
        'status', 'started_at', 'completed_at', 'flagged_for_exclusion',
    ]
    list_filter = ['study_assignment', 'wage_arm', 'occupation_pool', 'status', 'flagged_for_exclusion']
    search_fields = ['participant_code', 'prolific_id']
    readonly_fields = ['id', 'started_at']


@admin.register(Posting)
class PostingAdmin(admin.ModelAdmin):
    list_display = [
        'occupation_pool', 'company_name', 'signal_type',
        'salary_high_text', 'salary_low_text',
    ]
    list_filter = ['occupation_pool', 'signal_type']


admin.site.register(Demographics)
admin.site.register(IndividualDifferences)


@admin.register(RankingResponse)
class RankingResponseAdmin(admin.ModelAdmin):
    list_display = ['participant', 'dimension', 'dimension_order', 'ranking_order', 'timestamp']
    list_filter = ['dimension']
    raw_id_fields = ['participant']


@admin.register(CardSortCard)
class CardSortCardAdmin(admin.ModelAdmin):
    list_display = ['card_id', 'card_type', 'card_text', 'display_order']
    list_filter = ['card_type']


@admin.register(CardSortResponse)
class CardSortResponseAdmin(admin.ModelAdmin):
    list_display = ['participant', 'posting', 'stage', 'cards_selected', 'keep_original', 'timestamp']
    list_filter = ['stage', 'keep_original']
    raw_id_fields = ['participant', 'posting']


@admin.register(HiringManagerCard)
class HiringManagerCardAdmin(admin.ModelAdmin):
    list_display = ['card_id', 'card_type', 'card_text', 'display_order']
    list_filter = ['card_type']


@admin.register(HiringManagerResponse)
class HiringManagerResponseAdmin(admin.ModelAdmin):
    list_display = ['participant', 'posting', 'stage', 'cards_selected', 'would_change', 'timestamp']
    list_filter = ['stage', 'would_change']
    raw_id_fields = ['participant', 'posting']


@admin.register(BucketSortPhrase)
class BucketSortPhraseAdmin(admin.ModelAdmin):
    list_display = ['phrase_id', 'phrase_text', 'expected_bucket', 'difficulty', 'is_active']
    list_filter = ['difficulty', 'expected_bucket', 'is_active']
    search_fields = ['phrase_text']


@admin.register(BucketSortResponse)
class BucketSortResponseAdmin(admin.ModelAdmin):
    list_display = ['participant', 'phrase', 'attempt', 'bucket_assigned', 'was_missed', 'time_on_phrase_ms']
    list_filter = ['was_missed', 'attempt']
    raw_id_fields = ['participant', 'phrase']


@admin.register(BucketSortReconciliation)
class BucketSortReconciliationAdmin(admin.ModelAdmin):
    list_display = ['participant', 'phrase', 'first_bucket', 'second_bucket', 'resolution']
    list_filter = ['resolution']
    raw_id_fields = ['participant', 'phrase']
