from django.urls import path

from .views import UserRegistrationView, LogoutView, UserLoginView, DashboardView


app_name = 'accounts'

urlpatterns = [
    path(
        "dashboard/", DashboardView.as_view(),
        name="dashboard"
    ),
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
]
