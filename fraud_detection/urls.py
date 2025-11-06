from django.urls import path
from .views import FraudAlertListView, mark_alert_reviewed

app_name = 'fraud_detection'

urlpatterns = [
    path('', FraudAlertListView.as_view(), name='alerts'),
    path('<int:alert_id>/review/', mark_alert_reviewed, name='mark_reviewed'),
]
