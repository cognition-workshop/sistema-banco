from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.AnalyticsDashboardView.as_view(), name='dashboard'),
    path('api/transaction-volume/', views.TransactionVolumeDataView.as_view(), name='transaction_volume_data'),
    path('api/transaction-types/', views.TransactionTypeDistributionView.as_view(), name='transaction_type_data'),
    path('api/top-users/', views.TopUsersView.as_view(), name='top_users_data'),
    path('export/csv/', views.ExportTransactionsCSVView.as_view(), name='export_csv'),
]
