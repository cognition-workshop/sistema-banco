from django.urls import path

from .views import AnalyticsDashboardView, ExportTransactionsCSVView

app_name = 'analytics'

urlpatterns = [
    path('', AnalyticsDashboardView.as_view(), name='dashboard'),
    path('export/csv/', ExportTransactionsCSVView.as_view(), name='export_csv'),
]
