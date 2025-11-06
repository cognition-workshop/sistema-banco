from django.core.management.base import BaseCommand
from banking_calendar.models import BankingHoliday
from datetime import date


class Command(BaseCommand):
    help = 'Carrega feriados brasileiros no banco de dados'
    
    def handle(self, *args, **options):
        holidays_2024 = [
            ('Ano Novo', date(2024, 1, 1), BankingHoliday.HOLIDAY_TYPE_FEDERAL),
            ('Carnaval', date(2024, 2, 13), BankingHoliday.HOLIDAY_TYPE_OPTIONAL),
            ('Sexta-feira Santa', date(2024, 3, 29), BankingHoliday.HOLIDAY_TYPE_FEDERAL),
            ('Tiradentes', date(2024, 4, 21), BankingHoliday.HOLIDAY_TYPE_FEDERAL),
            ('Dia do Trabalho', date(2024, 5, 1), BankingHoliday.HOLIDAY_TYPE_FEDERAL),
            ('Corpus Christi', date(2024, 5, 30), BankingHoliday.HOLIDAY_TYPE_OPTIONAL),
            ('Independência do Brasil', date(2024, 9, 7), BankingHoliday.HOLIDAY_TYPE_FEDERAL),
            ('Nossa Senhora Aparecida', date(2024, 10, 12), BankingHoliday.HOLIDAY_TYPE_FEDERAL),
            ('Finados', date(2024, 11, 2), BankingHoliday.HOLIDAY_TYPE_FEDERAL),
            ('Proclamação da República', date(2024, 11, 15), BankingHoliday.HOLIDAY_TYPE_FEDERAL),
            ('Consciência Negra', date(2024, 11, 20), BankingHoliday.HOLIDAY_TYPE_FEDERAL),
            ('Natal', date(2024, 12, 25), BankingHoliday.HOLIDAY_TYPE_FEDERAL),
        ]
        
        holidays_2025 = [
            ('Ano Novo', date(2025, 1, 1), BankingHoliday.HOLIDAY_TYPE_FEDERAL),
            ('Carnaval', date(2025, 3, 4), BankingHoliday.HOLIDAY_TYPE_OPTIONAL),
            ('Sexta-feira Santa', date(2025, 4, 18), BankingHoliday.HOLIDAY_TYPE_FEDERAL),
            ('Tiradentes', date(2025, 4, 21), BankingHoliday.HOLIDAY_TYPE_FEDERAL),
            ('Dia do Trabalho', date(2025, 5, 1), BankingHoliday.HOLIDAY_TYPE_FEDERAL),
            ('Corpus Christi', date(2025, 6, 19), BankingHoliday.HOLIDAY_TYPE_OPTIONAL),
            ('Independência do Brasil', date(2025, 9, 7), BankingHoliday.HOLIDAY_TYPE_FEDERAL),
            ('Nossa Senhora Aparecida', date(2025, 10, 12), BankingHoliday.HOLIDAY_TYPE_FEDERAL),
            ('Finados', date(2025, 11, 2), BankingHoliday.HOLIDAY_TYPE_FEDERAL),
            ('Proclamação da República', date(2025, 11, 15), BankingHoliday.HOLIDAY_TYPE_FEDERAL),
            ('Consciência Negra', date(2025, 11, 20), BankingHoliday.HOLIDAY_TYPE_FEDERAL),
            ('Natal', date(2025, 12, 25), BankingHoliday.HOLIDAY_TYPE_FEDERAL),
        ]
        
        all_holidays = holidays_2024 + holidays_2025
        created_count = 0
        
        for name, holiday_date, holiday_type in all_holidays:
            holiday, created = BankingHoliday.objects.get_or_create(
                name=name,
                date=holiday_date,
                defaults={'holiday_type': holiday_type, 'is_recurring': True}
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Criado: {holiday}'))
        
        self.stdout.write(self.style.SUCCESS(f'\nTotal de {created_count} feriados criados.'))
