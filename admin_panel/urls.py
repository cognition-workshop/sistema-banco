from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AdminTokenObtainPairView,
    UserManagementViewSet,
    TransactionViewSet,
    FraudRuleViewSet,
    FraudAlertViewSet,
    AnalyticsViewSet,
    ReportViewSet,
    SystemHealthViewSet,
    AuditLogViewSet,
)

app_name = 'admin_panel'

router = DefaultRouter()
router.register(r'users', UserManagementViewSet, basename='user')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'fraud-rules', FraudRuleViewSet, basename='fraud-rule')
router.register(r'fraud-alerts', FraudAlertViewSet, basename='fraud-alert')
router.register(r'analytics', AnalyticsViewSet, basename='analytics')
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'health', SystemHealthViewSet, basename='health')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')

urlpatterns = [
    path('auth/login/', AdminTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]
