from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView

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
