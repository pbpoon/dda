from django.contrib import admin
from .models import Batch, Quarry, Category,  Product


@admin.register(Product)
class SNAdmin(admin.ModelAdmin):
    list_display = ('name', 'batch', 'quarry', 'category')


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Quarry)
class QuarryAdmin(admin.ModelAdmin):
    list_display = ('name', 'desc')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
