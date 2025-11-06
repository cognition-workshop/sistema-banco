from datetime import datetime, timedelta
from django.utils import timezone
from localization.models import Feriado


class CalendarioService:
    """Serviço para operações de calendário bancário"""
    
    @staticmethod
    def eh_dia_util(data):
        """Verifica se uma data é dia útil (não é sábado, domingo ou feriado)"""
        if data.weekday() >= 5:
            return False
        
        if Feriado.objects.filter(data=data).exists():
            return False
        
        return True
    
    @staticmethod
    def proximo_dia_util(data):
        """Retorna o próximo dia útil a partir de uma data"""
        data_atual = data
        while not CalendarioService.eh_dia_util(data_atual):
            data_atual += timedelta(days=1)
        return data_atual
    
    @staticmethod
    def calcular_prazo_dias_uteis(data_inicio, dias_uteis):
        """Calcula uma data futura considerando apenas dias úteis"""
        data_atual = data_inicio
        dias_contados = 0
        
        while dias_contados < dias_uteis:
            data_atual += timedelta(days=1)
            if CalendarioService.eh_dia_util(data_atual):
                dias_contados += 1
        
        return data_atual
    
    @staticmethod
    def contar_dias_uteis(data_inicio, data_fim):
        """Conta o número de dias úteis entre duas datas"""
        if data_inicio > data_fim:
            raise ValueError('Data inicial deve ser anterior à data final.')
        
        dias_uteis = 0
        data_atual = data_inicio
        
        while data_atual <= data_fim:
            if CalendarioService.eh_dia_util(data_atual):
                dias_uteis += 1
            data_atual += timedelta(days=1)
        
        return dias_uteis
    
    @staticmethod
    def listar_feriados(ano=None, tipo=None):
        """Lista feriados bancários"""
        queryset = Feriado.objects.all()
        
        if ano:
            queryset = queryset.filter(data__year=ano)
        
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        return queryset.order_by('data')
    
    @staticmethod
    def adicionar_feriado(nome, data, tipo='NACIONAL', recorrente=False):
        """Adiciona um novo feriado"""
        feriado, created = Feriado.objects.get_or_create(
            data=data,
            defaults={
                'nome': nome,
                'tipo': tipo,
                'recorrente': recorrente
            }
        )
        return feriado, created
