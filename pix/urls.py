from django.urls import path
from .views import PixKeyCreateView, PixKeyListView, PixTransferView, generate_pix_qr_code

app_name = 'pix'

urlpatterns = [
    path('register-key/', PixKeyCreateView.as_view(), name='register_key'),
    path('keys/', PixKeyListView.as_view(), name='list_keys'),
    path('transfer/', PixTransferView.as_view(), name='transfer'),
    path('qr-code/<int:key_id>/', generate_pix_qr_code, name='qr_code'),
]
