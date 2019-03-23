from django.contrib import admin
from .models import Invoice, Payment
# Register your models here.


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ()