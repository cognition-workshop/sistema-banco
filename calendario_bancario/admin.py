from django.contrib import admin
from .models import FeriadoBancario


@admin.register(FeriadoBancario)
class FeriadoBancarioAdmin(admin.ModelAdmin):
    list_display = ['data', 'nome', 'tipo', 'ativo']
    list_filter = ['tipo', 'ativo', 'data']
    search_fields = ['nome']
    date_hierarchy = 'data'
