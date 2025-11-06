from django.contrib import admin

from transactions.models import Transaction
from accounts.admin import admin_site

admin_site.register(Transaction)
