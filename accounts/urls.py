from django.urls import path

from .views import (
    UserRegistrationView, LogoutView, UserLoginView,
    UserManagementListView, UserEditView, UserSuspendToggleView
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
        "admin-users/",
        UserManagementListView.as_view(),
        name="admin_user_list"
    ),
    path(
        "admin-users/<int:pk>/edit/",
        UserEditView.as_view(),
        name="admin_user_edit"
    ),
    path(
        "admin-users/<int:pk>/suspend/",
        UserSuspendToggleView.as_view(),
        name="admin_user_suspend"
    ),
]
