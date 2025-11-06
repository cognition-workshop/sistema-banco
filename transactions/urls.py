from django.urls import path

from .views import (
    DepositMoneyView,
    WithdrawMoneyView,
    TransactionRepostView,
    PixKeyManagementView,
    PixTransferView,
    PixQRCodeGenerateView,
    PixQRCodePayView,
    PixTransactionHistoryView,
)


app_name = 'transactions'


urlpatterns = [
    path("deposit/", DepositMoneyView.as_view(), name="deposit_money"),
    path("report/", TransactionRepostView.as_view(), name="transaction_report"),
    path("withdraw/", WithdrawMoneyView.as_view(), name="withdraw_money"),
    path("pix/keys/", PixKeyManagementView.as_view(), name="pix_keys"),
    path("pix/transfer/", PixTransferView.as_view(), name="pix_transfer"),
    path("pix/qrcode/generate/", PixQRCodeGenerateView.as_view(), name="pix_qrcode_generate"),
    path("pix/qrcode/pay/", PixQRCodePayView.as_view(), name="pix_qrcode_pay"),
    path("pix/history/", PixTransactionHistoryView.as_view(), name="pix_history"),
]
