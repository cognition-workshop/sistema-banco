from django.contrib import admin

from transactions.models import Transaction, BankingHoliday

admin.site.register(Transaction)
admin.site.register(BankingHoliday)
