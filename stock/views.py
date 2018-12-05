from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from cart.cart import Cart
from product.models import Slab
from public.forms import LocationForm
from public.views import OrderItemEditMixin
from .models import Warehouse, Location, Stock


class WarehouseListView(ListView):
    model = Warehouse


class WarehouseDetailView(DetailView):
    model = Warehouse


class WarehouseCreateView(CreateView):
    model = Warehouse
    fields = '__all__'
    template_name = 'stock/form.html'


class WarehouseUpdateView(UpdateView):
    model = Warehouse
    fields = '__all__'
    template_name = 'stock/form.html'


class LocationEditMixin:
    model = Location
    form_class = LocationForm

    def get_initial(self):
        initial = super(LocationEditMixin, self).get_initial()
        warehouse_id = self.request.GET.get('warehouse_id')
        if warehouse_id:
            initial.update({'warehouse': warehouse_id})
        return initial


class LocationCreateView(LocationEditMixin, CreateView):
    pass


class LocationUpdateView(LocationEditMixin, UpdateView):
    pass


class LocationListView(ListView):
    model = Location


class LocationDetail(DetailView):
    model = Location


class StockListView(ListView):
    model = Stock


class StockDetailView(DetailView):
    model = Stock
    template_name = 'stock/detail.html'

    def post(self, *args, **kwargs):
        slab_list = self.request.POST.getlist('select')
        product_id = self.request.POST.get('product')
        cart = Cart(self.request)
        cart.add(product_id, slab_id_list=slab_list)
        return JsonResponse({'state': 'ok'})


class StockSlabsView(DetailView):
    model = Stock
    template_name = 'package_list.html'
    context_object_name = 'package'
