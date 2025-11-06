from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.AdminDashboardView.as_view(), name='dashboard'),
    path('users/', views.UserManagementView.as_view(), name='user_management'),
    path('users/<int:pk>/edit/', views.UserEditView.as_view(), name='user_edit'),
    path('users/<int:pk>/suspend/', views.suspend_user, name='user_suspend'),
    path('users/<int:pk>/reactivate/', views.reactivate_user, name='user_reactivate'),
    path('transactions/', views.TransactionMonitorView.as_view(), name='transaction_monitor'),
]
