from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import ChavePixViewSet, PixViewSet

router = DefaultRouter()
router.register(r'chaves', ChavePixViewSet, basename='chave-pix')
router.register(r'', PixViewSet, basename='pix')

app_name = 'pix'

urlpatterns = [
    path('', include(router.urls)),
]
