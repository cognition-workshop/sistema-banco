from datetime import datetime
from django.core.management.base import BaseCommand
from workalendar.america import Brazil
from transactions.models import BankingHoliday


class Command(BaseCommand):
    help = 'Populate Brazilian banking holidays using workalendar'

    def add_arguments(self, parser):
        parser.add_argument(
            '--years',
            type=int,
            default=2,
            help='Number of years to populate (default: 2 - current and next year)'
        )

    def handle(self, *args, **options):
        calendar = Brazil()
        current_year = datetime.now().year
        years_to_populate = options['years']
        
        total_created = 0
        total_updated = 0
        
        for year in range(current_year, current_year + years_to_populate):
            holidays = calendar.holidays(year)
            
            for holiday_date, holiday_name in holidays:
                obj, created = BankingHoliday.objects.update_or_create(
                    date=holiday_date,
                    defaults={
                        'name': holiday_name,
                        'is_national': True
                    }
                )
                if created:
                    total_created += 1
                else:
                    total_updated += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully populated holidays: {total_created} created, {total_updated} updated'
            )
        )
