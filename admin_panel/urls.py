from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/edit/', views.UserEditView.as_view(), name='user_edit'),
    path('users/<int:pk>/suspend/', views.UserSuspendView.as_view(), name='user_suspend'),
    path('transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    path('analytics/', views.AnalyticsDashboardView.as_view(), name='analytics'),
    path('fraud/rules/', views.FraudRuleListView.as_view(), name='fraud_rules'),
    path('fraud/rules/create/', views.FraudRuleCreateView.as_view(), name='fraud_rule_create'),
    path('fraud/alerts/', views.FraudAlertListView.as_view(), name='fraud_alerts'),
    path('system/health/', views.SystemHealthView.as_view(), name='system_health'),
]
