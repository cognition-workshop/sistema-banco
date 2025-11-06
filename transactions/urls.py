from django.urls import path

from .views import DepositMoneyView, WithdrawMoneyView, TransactionRepostView
from .irpf_views import IRPFReportView, IRPFGenerateView, IRPFExportView


app_name = 'transactions'


urlpatterns = [
    path("deposit/", DepositMoneyView.as_view(), name="deposit_money"),
    path("report/", TransactionRepostView.as_view(), name="transaction_report"),
    path("withdraw/", WithdrawMoneyView.as_view(), name="withdraw_money"),
    path("irpf/", IRPFReportView.as_view(), name="irpf_report"),
    path("irpf/generate/", IRPFGenerateView.as_view(), name="irpf_generate"),
    path("irpf/export/<int:report_id>/<str:format>/", IRPFExportView.as_view(), name="irpf_export"),
]
