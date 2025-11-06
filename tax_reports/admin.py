from django.contrib import admin
from .models import AnnualTaxReport


@admin.register(AnnualTaxReport)
class AnnualTaxReportAdmin(admin.ModelAdmin):
    list_display = ['account', 'year', 'total_deposits', 'total_interest', 'generated_at']
    list_filter = ['year']
    search_fields = ['account__account_no']
