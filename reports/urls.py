from django.urls import path

from .views import IRPFReportView, IRPFExportCSVView, IRPFExportPDFView


app_name = 'reports'


urlpatterns = [
    path('irpf/', IRPFReportView.as_view(), name='irpf_report'),
    path('irpf/csv/', IRPFExportCSVView.as_view(), name='irpf_export_csv'),
    path('irpf/pdf/', IRPFExportPDFView.as_view(), name='irpf_export_pdf'),
]
