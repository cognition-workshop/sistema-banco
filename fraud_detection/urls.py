from django.urls import path
from . import views

app_name = 'fraud_detection'

urlpatterns = [
    path('rules/', views.FraudRuleListView.as_view(), name='rule_list'),
    path('rules/create/', views.FraudRuleCreateView.as_view(), name='rule_create'),
    path('rules/<int:pk>/edit/', views.FraudRuleUpdateView.as_view(), name='rule_update'),
    path('rules/<int:pk>/delete/', views.FraudRuleDeleteView.as_view(), name='rule_delete'),
    
    path('alerts/', views.FraudAlertListView.as_view(), name='alert_list'),
    path('alerts/<int:pk>/', views.FraudAlertDetailView.as_view(), name='alert_detail'),
    path('alerts/<int:pk>/resolve/', views.FraudAlertResolveView.as_view(), name='alert_resolve'),
]
