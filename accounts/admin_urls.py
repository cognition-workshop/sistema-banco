from django.urls import path
from .views import AdminUserListView, AdminUserEditView, AdminUserToggleActiveView

app_name = "admin_users"

urlpatterns = [
    path("", AdminUserListView.as_view(), name="user_list"),
    path("<int:pk>/edit/", AdminUserEditView.as_view(), name="user_edit"),
    path("<int:pk>/status/", AdminUserToggleActiveView.as_view(), name="user_toggle_status"),
]
