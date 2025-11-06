from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import ChavePixViewSet, PixViewSet, anos_disponiveis_irpf, gerar_relatorio_irpf

app_name = 'transactions_api'

router = DefaultRouter()
router.register(r'chaves-pix', ChavePixViewSet, basename='chave-pix')
router.register(r'pix', PixViewSet, basename='pix')

urlpatterns = [
    path('', include(router.urls)),
    path('irpf/anos-disponiveis/', anos_disponiveis_irpf, name='anos-disponiveis-irpf'),
    path('irpf/gerar/<int:ano>/', gerar_relatorio_irpf, name='gerar-relatorio-irpf'),
]
