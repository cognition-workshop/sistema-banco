from django.urls import path
from .views import health_check_view, readiness_check_view

app_name = "core"

urlpatterns = [
    path("health/", health_check_view, name="health_check"),
    path("readiness/", readiness_check_view, name="readiness_check"),
]
