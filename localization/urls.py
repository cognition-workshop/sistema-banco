from django.urls import path, include
from rest_framework.routers import DefaultRouter
from localization import views

app_name = 'localization'

router = DefaultRouter()
router.register(r'usuarios', views.UserViewSet, basename='usuario')
router.register(r'pix/chaves', views.ChavePIXViewSet, basename='chave-pix')
router.register(r'pix/transferencias', views.TransacaoPIXViewSet, basename='transacao-pix')
router.register(r'calendario/feriados', views.FeriadoViewSet, basename='feriado')
router.register(r'audit/logs', views.AuditLogViewSet, basename='audit-log')
router.register(r'relatorios/irpf', views.RelatorioIRPFViewSet, basename='relatorio-irpf')

urlpatterns = [
    path('api/v1/', include(router.urls)),
]
