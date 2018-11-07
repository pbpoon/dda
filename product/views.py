from django.shortcuts import render
from django.views.generic import ListView, DetailView

from .models import Product, Category, Slab, PackageList


class ProductListView(ListView):
    model = Product


class ProductDetailView(DetailView):
    model = Product

