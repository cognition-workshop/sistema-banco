from django.urls import path
from .views import AnalyticsDashboardView, ReportListView, export_transactions_csv

app_name = 'analytics'

urlpatterns = [
    path('', AnalyticsDashboardView.as_view(), name='analytics_dashboard'),
    path('reports/', ReportListView.as_view(), name='report_list'),
    path('export/csv/', export_transactions_csv, name='export_csv'),
]
