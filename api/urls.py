from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, BankAccountViewSet, TransactionViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet)
router.register(r"accounts", BankAccountViewSet)
router.register(r"transactions", TransactionViewSet)

app_name = "api"

urlpatterns = [
    path("", include(router.urls)),
]
