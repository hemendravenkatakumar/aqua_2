from django.urls import path
from .views import BatchListView, WeeklySummaryView

urlpatterns = [
    path('', BatchListView.as_view(), name='batch-list'),
    path('weekly/', WeeklySummaryView.as_view(), name='weekly-summary'),
]
