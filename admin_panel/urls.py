from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('login/', views.AdminLoginView.as_view(), name='login'),
    path('logout/', views.AdminLogoutView.as_view(), name='logout'),
    path('', views.AdminDashboardView.as_view(), name='dashboard'),
    
    path('users/', views.UsersDashboardView.as_view(), name='users_dashboard'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/edit/', views.UserEditView.as_view(), name='user_edit'),
    path('users/bulk-action/', views.UserBulkActionView.as_view(), name='user_bulk_action'),
    path('users/export/', views.UserExportView.as_view(), name='user_export'),
    
    path('transactions/', views.TransactionsDashboardView.as_view(), name='transactions_dashboard'),
    
    path('analytics/', views.AnalyticsDashboardView.as_view(), name='analytics_dashboard'),
    path('analytics/export/', views.AnalyticsExportView.as_view(), name='analytics_export'),
    
    path('fraud/', views.FraudDashboardView.as_view(), name='fraud_dashboard'),
    path('fraud/alerts/<int:pk>/', views.FraudAlertDetailView.as_view(), name='fraud_alert_detail'),
    
    path('health/', views.HealthDashboardView.as_view(), name='health_dashboard'),
]
