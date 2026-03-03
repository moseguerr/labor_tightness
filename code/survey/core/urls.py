from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Entry point
    path('', views.LandingView.as_view(), name='landing'),
    path('consent/', views.ConsentView.as_view(), name='consent'),

    # Study 1
    path('study1/instructions/', views.Study1InstructionsView.as_view(),
         name='study1_instructions'),
    path('study1/practice/<int:item_num>/', views.Study1PracticeView.as_view(),
         name='study1_practice'),
    path('study1/classify/<int:item_num>/', views.Study1ClassifyView.as_view(),
         name='study1_classify'),
    path('study1/post-task/', views.Study1PostTaskView.as_view(),
         name='study1_post_task'),

    # Transition (combined session only)
    path('transition/', views.TransitionView.as_view(), name='transition'),

    # Study 2
    path('study2/instructions/', views.Study2InstructionsView.as_view(),
         name='study2_instructions'),
    path('study2/posting/<int:posting_num>/', views.Study2PostingPageView.as_view(),
         name='study2_posting'),
    path('study2/manipulation-checks/', views.ManipulationChecksView.as_view(),
         name='manipulation_checks'),
    path('study2/ranking/<str:dimension>/', views.Study2RankingView.as_view(),
         name='study2_ranking'),
    path('study2/post-ranking/', views.PostRankingView.as_view(),
         name='post_ranking'),
    path('study2/individual-differences/', views.IndividualDifferencesView.as_view(),
         name='individual_differences'),

    # Demographics & Debrief
    path('demographics/', views.DemographicsView.as_view(), name='demographics'),
    path('debrief/', views.DebriefView.as_view(), name='debrief'),

    # Withdrawal
    path('withdraw/', views.WithdrawView.as_view(), name='withdraw'),

    # Researcher dashboard (staff only)
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/export/<str:fmt>/', views.ExportDataView.as_view(),
         name='export_data'),
]
