from django.core.management.base import BaseCommand
from datetime import date
from core.models import FeriadoBancario


class Command(BaseCommand):
    help = 'Populate Brazilian banking holidays'
    
    def handle(self, *args, **options):
        current_year = date.today().year
        
        feriados = [
            (1, 1, 'Ano Novo', True),
            (4, 21, 'Tiradentes', True),
            (5, 1, 'Dia do Trabalho', True),
            (9, 7, 'Independência do Brasil', True),
            (10, 12, 'Nossa Senhora Aparecida', True),
            (11, 2, 'Finados', True),
            (11, 15, 'Proclamação da República', True),
            (12, 25, 'Natal', True),
        ]
        
        for mes, dia, descricao, recorrente in feriados:
            FeriadoBancario.objects.get_or_create(
                data=date(current_year, mes, dia),
                defaults={
                    'descricao': descricao,
                    'tipo': 'NACIONAL',
                    'recorrente': recorrente
                }
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully populated {len(feriados)} holidays')
        )
