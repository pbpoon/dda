from django.contrib import admin
from .models import Invoice
# Register your models here.


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    pass