from django.core.management.base import BaseCommand
from django.db import connection
from django.apps import apps
from datetime import datetime
import sys

class Command(BaseCommand):
    help = 'Exibe o histórico completo de migrations aplicadas no sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--app',
            type=str,
            help='Filtrar por app específica',
        )
        parser.add_argument(
            '--format',
            type=str,
            default='table',
            choices=['table', 'json'],
            help='Formato de saída (table ou json)',
        )

    def handle(self, *args, **options):
        app_filter = options.get('app')
        output_format = options.get('format')
        
        with connection.cursor() as cursor:
            if app_filter:
                cursor.execute(
                    "SELECT app, name, applied FROM django_migrations WHERE app = %s ORDER BY applied DESC",
                    [app_filter]
                )
            else:
                cursor.execute(
                    "SELECT app, name, applied FROM django_migrations ORDER BY applied DESC"
                )
            migrations = cursor.fetchall()
        
        if output_format == 'json':
            import json
            data = [
                {
                    'app': m[0],
                    'name': m[1],
                    'applied': m[2].isoformat() if m[2] else None
                }
                for m in migrations
            ]
            self.stdout.write(json.dumps(data, indent=2))
        else:
            self.stdout.write(self.style.SUCCESS('\n=== Histórico de Migrations ===\n'))
            self.stdout.write(f"{'App':<20} {'Migration':<50} {'Aplicada em':<30}")
            self.stdout.write('-' * 100)
            
            for app, name, applied in migrations:
                applied_str = applied.strftime('%Y-%m-%d %H:%M:%S') if applied else 'N/A'
                self.stdout.write(f"{app:<20} {name:<50} {applied_str:<30}")
            
            self.stdout.write(f"\nTotal: {len(migrations)} migrations aplicadas")
