from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.admin_dashboard_view, name='dashboard'),
    path('users/', views.user_list_view, name='user_list'),
    path('users/<int:user_id>/', views.user_detail_view, name='user_detail'),
    path('users/<int:user_id>/suspend/', views.suspend_user_view, name='suspend_user'),
    path('users/<int:user_id>/unsuspend/', views.unsuspend_user_view, name='unsuspend_user'),
]
