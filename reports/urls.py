from django.urls import path
from .views import RelatorioIRPFView, exportar_irpf_pdf, exportar_irpf_csv

app_name = 'reports'

urlpatterns = [
    path('irpf/', RelatorioIRPFView.as_view(), name='irpf'),
    path('irpf/pdf/', exportar_irpf_pdf, name='irpf_pdf'),
    path('irpf/csv/', exportar_irpf_csv, name='irpf_csv'),
]
