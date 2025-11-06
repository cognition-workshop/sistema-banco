from django.urls import path
from .views import PixKeyCreateView, PixKeyListView, PixTransferView, PixQRCodeView

app_name = 'pix'

urlpatterns = [
    path('keys/', PixKeyListView.as_view(), name='pix_key_list'),
    path('keys/register/', PixKeyCreateView.as_view(), name='pix_key_register'),
    path('transfer/', PixTransferView.as_view(), name='pix_transfer'),
    path('qrcode/<int:pk>/', PixQRCodeView.as_view(), name='pix_qrcode'),
]
