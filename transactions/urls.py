from django.urls import path

from .views import DepositMoneyView, WithdrawMoneyView, TransactionRepostView, PIXFormView
from .api import BalanceAPIView, ValidateAmountAPIView


app_name = 'transactions'


urlpatterns = [
    path("deposit/", DepositMoneyView.as_view(), name="deposit_money"),
    path("report/", TransactionRepostView.as_view(), name="transaction_report"),
    path("withdraw/", WithdrawMoneyView.as_view(), name="withdraw_money"),
    path("pix/", PIXFormView.as_view(), name="pix_form"),
    path("api/balance/", BalanceAPIView.as_view(), name="api_balance"),
    path("api/validate-amount/", ValidateAmountAPIView.as_view(), name="api_validate_amount"),
]
