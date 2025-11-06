from django.urls import path

from .views import DepositMoneyView, WithdrawMoneyView, TransactionRepostView
from .pix_views import PixKeyListView, PixKeyRegisterView, PixTransferView
from .irpf_views import IRPFReportView, IRPFReportCSVView


app_name = 'transactions'


urlpatterns = [
    path("deposit/", DepositMoneyView.as_view(), name="deposit_money"),
    path("report/", TransactionRepostView.as_view(), name="transaction_report"),
    path("withdraw/", WithdrawMoneyView.as_view(), name="withdraw_money"),
    path("pix/keys/", PixKeyListView.as_view(), name="pix_keys"),
    path("pix/register/", PixKeyRegisterView.as_view(), name="pix_register"),
    path("pix/transfer/", PixTransferView.as_view(), name="pix_transfer"),
    path("irpf/<int:year>/", IRPFReportView.as_view(), name="irpf_report"),
    path("irpf/<int:year>/csv/", IRPFReportCSVView.as_view(), name="irpf_csv"),
]
