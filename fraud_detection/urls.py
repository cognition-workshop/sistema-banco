from django.urls import path
from . import views

app_name = 'fraud_detection'

urlpatterns = [
    path('', views.FraudAlertListView.as_view(), name='alert_list'),
    path('<int:pk>/', views.FraudAlertDetailView.as_view(), name='alert_detail'),
    path('<int:pk>/resolve/', views.mark_alert_resolved, name='mark_resolved'),
    path('<int:pk>/false-positive/', views.mark_alert_false_positive, name='mark_false_positive'),
]
