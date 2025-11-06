from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('export/csv/', views.ExportCSVView.as_view(), name='export_csv'),
    path('export/pdf/', views.ExportPDFView.as_view(), name='export_pdf'),
    path('export/excel/', views.ExportExcelView.as_view(), name='export_excel'),
]
