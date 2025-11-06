from django.urls import path

from .views import UserRegistrationView, LogoutView, UserLoginView
from .admin_views import UserListView, toggle_user_suspension


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
        "admin/users/", UserListView.as_view(),
        name="admin_user_list"
    ),
    path(
        "admin/users/<int:user_id>/suspend/", toggle_user_suspension,
        name="toggle_suspension"
    ),
]
