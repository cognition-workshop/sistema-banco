from django.core.management.base import BaseCommand
from admin_panel.models import FraudRule
from admin_panel.constants import (
    FRAUD_SUSPICIOUS_WITHDRAWAL,
    FRAUD_UNUSUAL_HOURS,
    FRAUD_REPEATED_TRANSACTIONS,
    FRAUD_EXCEEDS_MAX_AMOUNT,
    SEVERITY_HIGH,
    SEVERITY_MEDIUM
)


class Command(BaseCommand):
    help = 'Create default fraud detection rules'
    
    def handle(self, *args, **options):
        rules = [
            {
                'name': 'Large Withdrawal Detection',
                'rule_type': FRAUD_SUSPICIOUS_WITHDRAWAL,
                'parameters': {
                    'amount_threshold': 5000,
                    'percentage_of_balance': 80
                },
                'severity': SEVERITY_HIGH,
                'is_active': True
            },
            {
                'name': 'After Hours Transaction',
                'rule_type': FRAUD_UNUSUAL_HOURS,
                'parameters': {
                    'start_hour': 22,
                    'end_hour': 6
                },
                'severity': SEVERITY_MEDIUM,
                'is_active': True
            },
            {
                'name': 'Repeated Transaction Pattern',
                'rule_type': FRAUD_REPEATED_TRANSACTIONS,
                'parameters': {
                    'time_window_minutes': 30,
                    'count_threshold': 3,
                    'amount_threshold': 100
                },
                'severity': SEVERITY_HIGH,
                'is_active': True
            },
            {
                'name': 'Exceeds Maximum After Hours',
                'rule_type': FRAUD_EXCEEDS_MAX_AMOUNT,
                'parameters': {
                    'max_amount': 10000,
                    'time_restriction_start': 22,
                    'time_restriction_end': 6
                },
                'severity': SEVERITY_HIGH,
                'is_active': True
            }
        ]
        
        created_count = 0
        for rule_data in rules:
            rule, created = FraudRule.objects.get_or_create(
                name=rule_data['name'],
                defaults=rule_data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created fraud rule: {rule.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Fraud rule already exists: {rule.name}'))
        
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} new fraud rules'))
