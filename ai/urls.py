from django.urls import path
from .views import ChatView, ClearChatHistoryView

urlpatterns = [
    path('chat/', ChatView.as_view(), name='ai-chat'),
    path('clear/', ClearChatHistoryView.as_view(), name='ai-clear'),
]
