from django.contrib import admin
from .models import Partner, Province, City


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    pass
