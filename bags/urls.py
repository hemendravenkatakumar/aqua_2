from django.urls import path
from .views import BagListView, BagDetailView, BagStatsView

urlpatterns = [
    path('', BagListView.as_view(), name='bag-list'),
    path('stats/', BagStatsView.as_view(), name='bag-stats'),
    path('<str:pk>/', BagDetailView.as_view(), name='bag-detail'),
]
