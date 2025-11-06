"""banking_system URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path

from core.views import HomeView
from core import health


urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("admin/", admin.site.urls),
    path("transactions/", include("transactions.urls", namespace="transactions")),
    path("health/", health.health_check, name="health"),
    path("health/db/", health.health_check_database, name="health_db"),
    path("health/redis/", health.health_check_redis, name="health_redis"),
    path("health/detailed/", health.health_check_detailed, name="health_detailed"),
]

handler404 = "core.views.handler404"
handler500 = "core.views.handler500"
handler403 = "core.views.handler403"
