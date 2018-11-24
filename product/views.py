from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, HttpResponse
from django.views.generic import ListView, DetailView
from utils import obj_to_dict

from .models import Product, Category, Slab, PackageList


def get_product_info(request):
    product_id = request.GET.get('value')
    product = get_object_or_404(Product, pk=product_id)
    data = obj_to_dict(product)
    if product.uom == 't':
        data['quantity'] = data['weight']
    else:
        data['quantity'] = data['m3']
    data['piece'] = 1
    return JsonResponse(data)


class ProductListView(ListView):
    model = Product


class ProductDetailView(DetailView):
    model = Product
