from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('api/', include('users.urls')),
    path('api/bags/', include('bags.urls')),
    path('api/vehicles/', include('vehicles.urls')),
    path('api/batches/', include('history.urls')),
    path('api/ai/', include('ai.urls')),
]
