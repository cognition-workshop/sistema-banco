from django.contrib import admin

from transactions.models import Transaction
from .irpf_models import IRPFReport

admin.site.register(Transaction)


@admin.register(IRPFReport)
class IRPFReportAdmin(admin.ModelAdmin):
    list_display = ['user', 'year', 'total_deposits', 'total_withdrawals', 'closing_balance', 'generated_at']
    list_filter = ['year']
    search_fields = ['user__email']
