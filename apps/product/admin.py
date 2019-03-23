from django.contrib import admin
from .models import Batch, Quarry, Category, Product, Block


# @admin.register(Product)
# class SNAdmin(admin.ModelAdmin):
#     list_display = ('name',)


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Quarry)
class QuarryAdmin(admin.ModelAdmin):
    list_display = ('name', 'desc')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Block)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
