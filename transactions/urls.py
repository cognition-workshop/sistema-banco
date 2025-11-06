from django.urls import path

from .views import DepositMoneyView, WithdrawMoneyView, TransactionRepostView
from .pix_views import (
    PIXKeyListView, PIXKeyCreateView, PIXKeyDeleteView,
    PIXTransferView, PIXQRCodeGenerateView, PIXQRCodeView
)


app_name = 'transactions'


urlpatterns = [
    path("deposit/", DepositMoneyView.as_view(), name="deposit_money"),
    path("report/", TransactionRepostView.as_view(), name="transaction_report"),
    path("withdraw/", WithdrawMoneyView.as_view(), name="withdraw_money"),
    
    path("pix/keys/", PIXKeyListView.as_view(), name="pix_key_list"),
    path("pix/keys/create/", PIXKeyCreateView.as_view(), name="pix_key_create"),
    path("pix/keys/<int:pk>/delete/", PIXKeyDeleteView.as_view(), name="pix_key_delete"),
    path("pix/transfer/", PIXTransferView.as_view(), name="pix_transfer"),
    path("pix/qr-code/generate/", PIXQRCodeGenerateView.as_view(), name="pix_qr_code_generate"),
    path("pix/qr-code/<int:pk>/", PIXQRCodeView.as_view(), name="pix_qr_code_view"),
]
