#!/usr/bin/env python
"""Backup the SQLite database before performing migrations rollback"""
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / 'db.sqlite3'

def backup_database():
    """Create a timestamped backup of the database"""
    if not DB_PATH.exists():
        print("❌ Erro: Arquivo de banco de dados não encontrado em:", DB_PATH)
        print("Execute 'python manage.py migrate' primeiro para criar o banco de dados.")
        sys.exit(1)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'db.sqlite3.backup.{timestamp}'
    backup_path = BASE_DIR / backup_filename
    
    try:
        print(f"🔄 Criando backup de {DB_PATH.name}...")
        
        shutil.copy2(DB_PATH, backup_path)
        
        original_size = DB_PATH.stat().st_size
        backup_size = backup_path.stat().st_size
        
        print("✅ Backup criado com sucesso!")
        print(f"📁 Local do backup: {backup_path}")
        print(f"📊 Tamanho: {backup_size:,} bytes")
        
        if original_size == backup_size:
            print("✓ Verificação: Tamanhos coincidem")
        else:
            print("⚠️  Aviso: Tamanhos não coincidem")
            print(f"   Original: {original_size:,} bytes")
            print(f"   Backup: {backup_size:,} bytes")
            
        print(f"\n💡 Para restaurar, execute:")
        print(f"   cp {backup_filename} db.sqlite3")
            
        return str(backup_path)
        
    except Exception as e:
        print(f"❌ Erro ao criar backup: {e}")
        sys.exit(1)

if __name__ == '__main__':
    print("="*70)
    print("BACKUP DO BANCO DE DADOS")
    print("="*70)
    print()
    
    backup_path = backup_database()
    
    print()
    print("="*70)
