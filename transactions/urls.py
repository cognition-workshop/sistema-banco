from django.urls import path

from .views import DepositMoneyView, WithdrawMoneyView, TransactionRepostView, DashboardView


app_name = 'transactions'


urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("deposit/", DepositMoneyView.as_view(), name="deposit_money"),
    path("report/", TransactionRepostView.as_view(), name="transaction_report"),
    path("withdraw/", WithdrawMoneyView.as_view(), name="withdraw_money"),
]
