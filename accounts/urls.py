from django.urls import path

from .views import (
    UserRegistrationView, LogoutView, UserLoginView,
    UserListView, UserDetailView, UserUpdateView, UserSuspendView
)


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
        name="user_list"
    ),
    path(
        "admin/users/<int:pk>/", UserDetailView.as_view(),
        name="user_detail"
    ),
    path(
        "admin/users/<int:pk>/edit/", UserUpdateView.as_view(),
        name="user_update"
    ),
    path(
        "admin/users/<int:pk>/suspend/", UserSuspendView.as_view(),
        name="user_suspend"
    ),
]
