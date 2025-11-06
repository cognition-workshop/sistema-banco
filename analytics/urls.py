from django.urls import path

from .views import (
    FinancialOverviewView,
    TransactionAnalysisView,
    AccountTypesView,
    InterestView,
    LimitsView,
    UsersView,
)


app_name = 'analytics'


urlpatterns = [
    path('financial-overview/', FinancialOverviewView.as_view(), name='financial_overview'),
    path('transaction-analysis/', TransactionAnalysisView.as_view(), name='transaction_analysis'),
    path('account-types/', AccountTypesView.as_view(), name='account_types'),
    path('interest/', InterestView.as_view(), name='interest'),
    path('limits/', LimitsView.as_view(), name='limits'),
    path('users/', UsersView.as_view(), name='users'),
]
