from django.urls import path

from .views import DepositMoneyView, WithdrawMoneyView, TransactionRepostView, BalanceQueryAPIView


app_name = 'transactions'


urlpatterns = [
    path("deposit/", DepositMoneyView.as_view(), name="deposit_money"),
    path("report/", TransactionRepostView.as_view(), name="transaction_report"),
    path("withdraw/", WithdrawMoneyView.as_view(), name="withdraw_money"),
    path("api/balance/", BalanceQueryAPIView.as_view(), name="balance_query_api"),
]
