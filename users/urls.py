from django.urls import path
from .views import VerifyOTPView, ProfileView

urlpatterns = [
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('me/', ProfileView.as_view(), name='me'),
]
