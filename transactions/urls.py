from django.urls import path

from .views import DepositMoneyView, WithdrawMoneyView, TransactionRepostView, IRPFReportView, AdminTransactionListView


app_name = 'transactions'


urlpatterns = [
    path("deposit/", DepositMoneyView.as_view(), name="deposit_money"),
    path("report/", TransactionRepostView.as_view(), name="transaction_report"),
    path("irpf/", IRPFReportView.as_view(), name="irpf_report"),
    path("withdraw/", WithdrawMoneyView.as_view(), name="withdraw_money"),
    path("admin-transactions/", AdminTransactionListView.as_view(), name="admin_transaction_list"),
]
