from django.core.management.base import BaseCommand
from datetime import date
from calendario_bancario.models import FeriadoBancario
from calendario_bancario.utils import calcular_feriados_moveis


class Command(BaseCommand):
    help = 'Update banking holidays for a given year'

    def add_arguments(self, parser):
        parser.add_argument('--ano', type=int, default=date.today().year)

    def handle(self, *args, **options):
        ano = options['ano']
        
        feriados_fixos = [
            (1, 1, 'Ano Novo'),
            (4, 21, 'Tiradentes'),
            (5, 1, 'Dia do Trabalho'),
            (9, 7, 'Independência do Brasil'),
            (10, 12, 'Nossa Senhora Aparecida'),
            (11, 2, 'Finados'),
            (11, 15, 'Proclamação da República'),
            (11, 20, 'Consciência Negra'),
            (12, 25, 'Natal'),
        ]
        
        for mes, dia, nome in feriados_fixos:
            data = date(ano, mes, dia)
            FeriadoBancario.objects.get_or_create(
                data=data,
                defaults={'nome': nome, 'tipo': 'NACIONAL', 'ativo': True}
            )
            self.stdout.write(self.style.SUCCESS(f'Created/Updated: {nome} - {data}'))
        
        feriados_moveis = calcular_feriados_moveis(ano)
        for data, nome in feriados_moveis:
            FeriadoBancario.objects.get_or_create(
                data=data,
                defaults={'nome': nome, 'tipo': 'NACIONAL', 'ativo': True}
            )
            self.stdout.write(self.style.SUCCESS(f'Created/Updated: {nome} - {data}'))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully updated holidays for {ano}'))
