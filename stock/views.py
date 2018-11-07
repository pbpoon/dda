from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView

from .models import Warehouse, Location


class WarehouseListView(ListView):
    model = Warehouse


class WarehouseDetailView(DetailView):
    model = Warehouse


class WarehouseCreateView(CreateView):
    model = Warehouse
    fields = '__all__'


class LocationListView(ListView):
    model = Location


class LocationDetail(DetailView):
    model = Location
