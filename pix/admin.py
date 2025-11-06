from django.contrib import admin
from .models import PixKey, PixTransaction, PixQRCode

admin.site.register(PixKey)
admin.site.register(PixTransaction)
admin.site.register(PixQRCode)
