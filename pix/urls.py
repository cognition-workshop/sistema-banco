from django.urls import path
from . import views

app_name = 'pix'

urlpatterns = [
    path('register-key/', views.PixKeyRegistrationView.as_view(), name='register_key'),
    path('keys/', views.PixKeyListView.as_view(), name='list_keys'),
    path('transfer/', views.pix_transfer_view, name='transfer'),
    path('generate-qrcode/', views.generate_qr_code_view, name='generate_qrcode'),
]
