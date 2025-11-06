from django.urls import path

from .views import DepositMoneyView, TransferMoneyView, WithdrawMoneyView, TransactionRepostView


app_name = 'transactions'


urlpatterns = [
    path("deposit/", DepositMoneyView.as_view(), name="deposit_money"),
    path("report/", TransactionRepostView.as_view(), name="transaction_report"),
    path("transfer/", TransferMoneyView.as_view(), name="transfer_money"),
    path("withdraw/", WithdrawMoneyView.as_view(), name="withdraw_money"),
]
