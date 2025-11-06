from django.urls import path
from .views import (
    CadastrarChavePixView,
    MinhasChavesPixView,
    DeletarChavePixView,
    TransferirPixView,
    HistoricoPixView,
)

app_name = 'pix'

urlpatterns = [
    path('cadastrar-chave/', CadastrarChavePixView.as_view(), name='cadastrar_chave'),
    path('minhas-chaves/', MinhasChavesPixView.as_view(), name='minhas_chaves'),
    path('deletar-chave/<int:pk>/', DeletarChavePixView.as_view(), name='deletar_chave'),
    path('transferir/', TransferirPixView.as_view(), name='transferir'),
    path('historico/', HistoricoPixView.as_view(), name='historico'),
]
