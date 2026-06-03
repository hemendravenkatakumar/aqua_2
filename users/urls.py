from django.urls import path
from .views import VerifyOTPView, ProfileView, RegisterView, LoginView

urlpatterns = [
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('me/', ProfileView.as_view(), name='me'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
]

