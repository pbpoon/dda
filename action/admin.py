from django.contrib import admin
from .models import WxConfig


@admin.register(WxConfig)
class WxConfigAdmin(admin.ModelAdmin):
    pass
