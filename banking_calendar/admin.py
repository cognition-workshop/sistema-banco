from django.contrib import admin
from .models import BankingHoliday


@admin.register(BankingHoliday)
class BankingHolidayAdmin(admin.ModelAdmin):
    list_display = ['date', 'name', 'is_national']
    list_filter = ['is_national', 'date']
    search_fields = ['name']
    date_hierarchy = 'date'
