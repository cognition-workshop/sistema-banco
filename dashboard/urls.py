from django.urls import path
from .views import ExecutiveDashboardView

app_name = 'dashboard'

urlpatterns = [
    path('', ExecutiveDashboardView.as_view(), name='executive_dashboard'),
]
