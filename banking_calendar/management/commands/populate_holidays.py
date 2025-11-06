from django.core.management.base import BaseCommand
from banking_calendar.models import BankingHoliday
from datetime import date


class Command(BaseCommand):
    help = 'Populate Brazilian banking holidays'

    def handle(self, *args, **kwargs):
        holidays_2024 = [
            (date(2024, 1, 1), 'Ano Novo', True),
            (date(2024, 2, 13), 'Carnaval', True),
            (date(2024, 3, 29), 'Sexta-feira Santa', True),
            (date(2024, 4, 21), 'Tiradentes', True),
            (date(2024, 5, 1), 'Dia do Trabalho', True),
            (date(2024, 5, 30), 'Corpus Christi', True),
            (date(2024, 9, 7), 'Independência do Brasil', True),
            (date(2024, 10, 12), 'Nossa Senhora Aparecida', True),
            (date(2024, 11, 2), 'Finados', True),
            (date(2024, 11, 15), 'Proclamação da República', True),
            (date(2024, 11, 20), 'Dia da Consciência Negra', True),
            (date(2024, 12, 25), 'Natal', True),
        ]

        for holiday_date, name, is_national in holidays_2024:
            BankingHoliday.objects.get_or_create(
                date=holiday_date,
                defaults={'name': name, 'is_national': is_national}
            )

        self.stdout.write(
            self.style.SUCCESS('Successfully populated banking holidays')
        )
