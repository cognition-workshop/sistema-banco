from django.urls import path

from .views import UserRegistrationView, LogoutView, UserLoginView, AdminLoginView
from .admin_views import UserManagementView, toggle_user_active


app_name = 'accounts'

urlpatterns = [
    path(
        "login/", UserLoginView.as_view(),
        name="user_login"
    ),
    path(
        "logout/", LogoutView.as_view(),
        name="user_logout"
    ),
    path(
        "register/", UserRegistrationView.as_view(),
        name="user_registration"
    ),
    path(
        "admin-portal/login/", AdminLoginView.as_view(),
        name="admin_login"
    ),
    path(
        "admin-portal/users/", UserManagementView.as_view(),
        name="user_management"
    ),
    path(
        "admin-portal/users/<int:user_id>/toggle-active/", toggle_user_active,
        name="toggle_user_active"
    ),
]
