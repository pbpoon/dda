from django import forms
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views.generic.edit import ModelFormMixin

from cart.cart import Cart
from product.models import Slab
from public.forms import LocationForm
from public.utils import Package
from public.views import OrderItemEditMixin, FilterListView
from public.widgets import SwitchesWidget
from .models import Warehouse, Location, Stock
from .filters import StockFilter


class WarehouseListView(ListView):
    model = Warehouse


class WarehouseDetailView(DetailView):
    model = Warehouse


class WarehouseEditMixin:
    model = Warehouse
    fields = '__all__'
    template_name = 'stock/form.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['is_production'].widget = SwitchesWidget()
        return form


class WarehouseCreateView(WarehouseEditMixin, CreateView):
    pass


class WarehouseUpdateView(WarehouseEditMixin, UpdateView):
    pass


class LocationEditMixin(ModelFormMixin, View):
    model = Location
    form_class = LocationForm
    template_name = 'item_form.html'

    def get_initial(self):
        initial = super().get_initial()
        self.warehouse = Warehouse.objects.get(pk=self.kwargs.get('warehouse_id'))
        if self.warehouse:
            initial.update({'warehouse': self.warehouse.id})
        initial['usage'] = 'internal'
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['parent'].queryset = self.warehouse.get_main_location().get_child()
        # form.fields['parent'].widget = forms.TypedChoiceField()
        return form

    def post(self, *args, **kwargs):
        self.object = self.get_object() if self.kwargs.get('pk') else None
        path = self.request.META.get('HTTP_REFERER')
        form = self.get_form()
        msg = '修改' if self.object else '添加'
        if form.is_valid():
            form.save()
            msg += '成功'
            messages.success(self.request, msg)
            # return redirect(path)
            return JsonResponse({'state': 'ok', 'url': path})
        msg += '失败'
        return HttpResponse(render_to_string(self.template_name, {'form': form, 'error': msg}))


class LocationCreateView(LocationEditMixin, CreateView):
    pass


class LocationUpdateView(LocationEditMixin, UpdateView):
    pass


class LocationListView(ListView):
    model = Location


class LocationDetail(DetailView):
    model = Location


class StockListView(FilterListView):
    model = Stock
    paginate_by = 10
    filter_class = StockFilter
    ordering = ('-created',)


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
    template_name = 'stock/package_list.html'

    def get_context_data(self, **kwargs):
        product = self.object.product
        slabs = self.object.items.all()
        package = Package(product, slabs)
        kwargs['package'] = package
        return super().get_context_data(**kwargs)
