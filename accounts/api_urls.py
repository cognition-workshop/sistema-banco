from django.urls import path
from .api_views import AccountBalanceView


app_name = 'accounts_api'

urlpatterns = [
    path('balance/', AccountBalanceView.as_view(), name='account_balance'),
]
