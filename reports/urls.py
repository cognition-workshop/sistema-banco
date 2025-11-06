from django.urls import path
from .views import IRPFReportView, IRPFExportCSVView

app_name = 'reports'

urlpatterns = [
    path('irpf/', IRPFReportView.as_view(), name='irpf_report'),
    path('irpf/export/', IRPFExportCSVView.as_view(), name='irpf_export'),
]
