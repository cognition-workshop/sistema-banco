from datetime import date
from django.test import TestCase
from localization.models import Feriado
from localization.services.calendario_service import CalendarioService


class CalendarioServiceTestCase(TestCase):
    """Testes para serviço de calendário"""
    
    def setUp(self):
        """Setup para testes"""
        Feriado.objects.get_or_create(
            data=date(2024, 1, 1),
            defaults={
                'nome': 'Ano Novo',
                'tipo': 'NACIONAL',
                'recorrente': True
            }
        )
        Feriado.objects.get_or_create(
            data=date(2024, 3, 15),
            defaults={
                'nome': 'Feriado Teste',
                'tipo': 'NACIONAL'
            }
        )
    
    def test_eh_dia_util(self):
        """Testa verificação de dia útil"""
        self.assertTrue(CalendarioService.eh_dia_util(date(2024, 3, 4)))
        
        self.assertFalse(CalendarioService.eh_dia_util(date(2024, 3, 2)))
        
        self.assertFalse(CalendarioService.eh_dia_util(date(2024, 1, 1)))
    
    def test_calcular_prazo_dias_uteis(self):
        """Testa cálculo de prazo em dias úteis"""
        data_inicio = date(2024, 3, 1)
        dias_uteis = 5
        
        data_fim = CalendarioService.calcular_prazo_dias_uteis(data_inicio, dias_uteis)
        
        self.assertGreater(data_fim, data_inicio)
    
    def test_contar_dias_uteis(self):
        """Testa contagem de dias úteis"""
        data_inicio = date(2024, 3, 1)
        data_fim = date(2024, 3, 8)
        
        dias_uteis = CalendarioService.contar_dias_uteis(data_inicio, data_fim)
        self.assertGreater(dias_uteis, 0)
    
    def test_proximo_dia_util(self):
        """Testa busca do próximo dia útil"""
        sabado = date(2024, 3, 2)
        proximo = CalendarioService.proximo_dia_util(sabado)
        
        self.assertGreater(proximo, sabado)
        self.assertTrue(CalendarioService.eh_dia_util(proximo))
