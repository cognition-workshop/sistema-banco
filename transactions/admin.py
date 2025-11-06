from accounts.admin import admin_site
from transactions.models import Transaction

admin_site.register(Transaction)
