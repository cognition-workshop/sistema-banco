from django.urls import path
from .views import SystemHealthView

app_name = 'monitoring'

urlpatterns = [
    path('', SystemHealthView.as_view(), name='health'),
]
