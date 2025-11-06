from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('irpf/', views.IRPFReportListView.as_view(), name='irpf_list'),
    path('irpf/generate/', views.generate_irpf_report_view, name='generate_irpf'),
    path('irpf/<int:report_id>/pdf/', views.download_irpf_pdf_view, name='download_pdf'),
    path('irpf/<int:report_id>/csv/', views.download_irpf_csv_view, name='download_csv'),
]
