from django.urls import path, include

app_name = 'monitoring'

urlpatterns = [
    path('', include('health_check.urls')),
]
