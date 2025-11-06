import os
import json
from datetime import datetime
from django.core import serializers
from django.apps import apps
from django.conf import settings
import shutil

class DatabaseBackup:
    """Utilitário para criar e restaurar backups do banco de dados"""
    
    def __init__(self, backup_dir='backups'):
        self.backup_dir = os.path.join(settings.BASE_DIR, backup_dir)
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self, description=''):
        """Cria um backup completo do banco de dados"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_{timestamp}"
        if description:
            backup_name += f"_{description}"
        
        backup_path = os.path.join(self.backup_dir, backup_name)
        os.makedirs(backup_path, exist_ok=True)
        
        data_file = os.path.join(backup_path, 'data.json')
        self._export_data(data_file)
        
        db_path = settings.DATABASES['default']['NAME']
        if os.path.exists(db_path):
            shutil.copy2(db_path, os.path.join(backup_path, 'db.sqlite3'))
        
        metadata = {
            'timestamp': timestamp,
            'description': description,
            'database_engine': settings.DATABASES['default']['ENGINE'],
        }
        with open(os.path.join(backup_path, 'metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return backup_path
    
    def _export_data(self, output_file):
        """Exporta todos os dados do banco em formato JSON"""
        all_models = []
        for app_config in apps.get_app_configs():
            for model in app_config.get_models():
                all_models.append(model)
        
        data = serializers.serialize('json', 
            [obj for model in all_models for obj in model.objects.all()],
            indent=2
        )
        
        with open(output_file, 'w') as f:
            f.write(data)
    
    def list_backups(self):
        """Lista todos os backups disponíveis"""
        backups = []
        if not os.path.exists(self.backup_dir):
            return backups
        
        for backup_name in os.listdir(self.backup_dir):
            backup_path = os.path.join(self.backup_dir, backup_name)
            metadata_file = os.path.join(backup_path, 'metadata.json')
            
            if os.path.isdir(backup_path) and os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                metadata['name'] = backup_name
                metadata['path'] = backup_path
                backups.append(metadata)
        
        return sorted(backups, key=lambda x: x['timestamp'], reverse=True)
