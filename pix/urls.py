from django.urls import path
from . import views

urlpatterns = [
    path('keys/', views.list_pix_keys, name='pix_keys'),
    path('keys/register/', views.register_pix_key, name='register_pix_key'),
    path('keys/<int:key_id>/delete/', views.delete_pix_key, name='delete_pix_key'),
    path('transfer/', views.create_pix_transfer, name='create_pix_transfer'),
    path('transactions/', views.list_pix_transactions, name='pix_transactions'),
    path('transactions/<uuid:transaction_id>/', views.pix_transaction_detail, name='pix_transaction_detail'),
]
