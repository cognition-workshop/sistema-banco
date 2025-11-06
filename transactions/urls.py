from django.urls import path

from .views import DepositMoneyView, WithdrawMoneyView, TransactionRepostView
from .admin_views import TransactionMonitoringView, export_transactions_csv


app_name = 'transactions'


urlpatterns = [
    path("deposit/", DepositMoneyView.as_view(), name="deposit_money"),
    path("report/", TransactionRepostView.as_view(), name="transaction_report"),
    path("withdraw/", WithdrawMoneyView.as_view(), name="withdraw_money"),
    path("admin-portal/transactions/", TransactionMonitoringView.as_view(), name="transaction_monitor"),
    path("admin-portal/transactions/export/", export_transactions_csv, name="transaction_export"),
]
