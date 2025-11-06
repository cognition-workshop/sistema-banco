from django.urls import path

from .views import UserRegistrationView, LogoutView, UserLoginView, AdminLoginView


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
]
