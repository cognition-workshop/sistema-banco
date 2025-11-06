from django.urls import path
from . import views

app_name = 'pix'

urlpatterns = [
    path('keys/', views.PixKeyListView.as_view(), name='key_list'),
    path('keys/register/', views.PixKeyCreateView.as_view(), name='key_register'),
    path('transfer/', views.PixTransferView.as_view(), name='transfer'),
    path('qrcode/generate/', views.PixQRCodeCreateView.as_view(), name='qrcode_generate'),
    path('qrcode/list/', views.PixQRCodeListView.as_view(), name='qrcode_list'),
]
