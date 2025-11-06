from django.urls import path
from .views import AnalyticsDashboardView, export_transactions_csv

app_name = 'analytics'

urlpatterns = [
    path('', AnalyticsDashboardView.as_view(), name='dashboard'),
    path('export/csv/', export_transactions_csv, name='export_csv'),
]
