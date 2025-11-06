from django.urls import path
from . import views

app_name = 'tax_reports'

urlpatterns = [
    path('', views.TaxReportListView.as_view(), name='report_list'),
    path('<int:pk>/', views.TaxReportDetailView.as_view(), name='report_detail'),
    path('generate/', views.TaxReportGenerateView.as_view(), name='generate'),
    path('<int:pk>/pdf/', views.download_pdf_report, name='download_pdf'),
    path('<int:pk>/csv/', views.export_csv_report, name='export_csv'),
]
