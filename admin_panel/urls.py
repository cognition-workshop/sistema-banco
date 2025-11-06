from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.AdminDashboardView.as_view(), name='dashboard'),
    
    path('users/', views.UserManagementView.as_view(), name='user_management'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/edit/', views.UserEditView.as_view(), name='user_edit'),
    path('users/<int:pk>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    
    path('transactions/', views.TransactionMonitoringView.as_view(), name='transaction_monitoring'),
    path('transactions/export-csv/', views.export_transactions_csv, name='export_transactions_csv'),
    path('transactions/export-excel/', views.export_transactions_excel, name='export_transactions_excel'),
    
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
    
    path('fraud/', views.FraudDetectionView.as_view(), name='fraud_detection'),
    path('fraud/<int:pk>/', views.FraudAlertDetailView.as_view(), name='fraud_alert_detail'),
    path('fraud/<int:pk>/review/', views.review_fraud_alert, name='review_fraud_alert'),
    
    path('health/', views.SystemHealthView.as_view(), name='system_health'),
    path('health/log/', views.log_system_health, name='log_system_health'),
]
