from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Entry
    path('', views.LandingView.as_view(), name='landing'),
    path('consent/', views.ConsentView.as_view(), name='consent'),

    # Posting reading (shared)
    path('read/', views.ReadPostingsView.as_view(), name='read_postings'),

    # Study 2: Ranking Task
    path('study2/instructions/', views.RankingInstructionsView.as_view(),
         name='ranking_instructions'),
    path('study2/rank/<int:dimension_num>/', views.RankingDimensionView.as_view(),
         name='study2_ranking'),

    # Study 2: Card Sort & Competition
    path('study2/card-sort/transition/', views.CardSortTransitionView.as_view(),
         name='card_sort_transition'),
    path('study2/card-sort/', views.CardSortView.as_view(),
         name='card_sort'),
    path('study2/competition/', views.CompetitionView.as_view(),
         name='competition'),

    # Study 3: Hiring Manager Card Sort & Competition
    path('study3/card-sort/transition/', views.HMCardSortTransitionView.as_view(),
         name='hm_card_sort_transition'),
    path('study3/card-sort/', views.HMCardSortView.as_view(),
         name='hm_card_sort'),
    path('study3/competition/', views.HMCompetitionView.as_view(),
         name='hm_competition'),

    # Study 1: Bucket Sort Game
    path('study1/transition/', views.BucketSortTransitionView.as_view(),
         name='bucket_sort_transition'),
    path('study1/instructions/', views.BucketSortInstructionsView.as_view(),
         name='bucket_sort_instructions'),
    path('study1/game/', views.BucketSortGameView.as_view(),
         name='bucket_sort_game'),
    path('study1/game/submit/', views.BucketSortSubmitView.as_view(),
         name='bucket_sort_submit'),
    path('study1/reconciliation/', views.BucketSortReconciliationView.as_view(),
         name='bucket_sort_reconciliation'),

    # Wrap-up
    path('final-questions/', views.FinalQuestionsView.as_view(),
         name='final_questions'),
    path('debrief/', views.DebriefView.as_view(), name='debrief'),
    path('complete/', views.CompleteView.as_view(), name='complete'),

    # Withdrawal
    path('withdraw/', views.WithdrawView.as_view(), name='withdraw'),
]
