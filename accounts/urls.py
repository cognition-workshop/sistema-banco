from django.urls import path

from .views import UserRegistrationView, LogoutView, UserLoginView
from .api_views import AccountBalanceAPIView


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
        "api/balance/", AccountBalanceAPIView.as_view(),
        name="api_balance"
    ),
]
