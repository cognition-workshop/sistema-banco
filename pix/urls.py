from django.urls import path

from .views import (
    PixKeyListView,
    PixKeyCreateView,
    PixTransferView,
    PixTransactionListView,
    PixQRCodeView,
)

app_name = 'pix'

urlpatterns = [
    path('keys/', PixKeyListView.as_view(), name='key_list'),
    path('keys/create/', PixKeyCreateView.as_view(), name='key_create'),
    path('transfer/', PixTransferView.as_view(), name='transfer'),
    path('transactions/', PixTransactionListView.as_view(), name='transaction_list'),
    path('qrcode/<int:key_id>/', PixQRCodeView.as_view(), name='qr_code'),
]
