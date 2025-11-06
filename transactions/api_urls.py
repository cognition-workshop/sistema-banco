from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import TransactionViewSet

router = DefaultRouter()
router.register(r'transactions', TransactionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
