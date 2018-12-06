from _decimal import Decimal

from django.db import transaction
from django.forms import inlineformset_factory
from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from cart.cart import Cart
from public.stock_operate import StockOperate
from public.views import OrderFormInitialEntryMixin, OrderItemEditMixin, OrderItemDeleteMixin, StateChangeMixin
from sales.forms import SalesOrderForm, SalesOrderItemForm, SalesOrderItemQuickForm
from sales.models import SalesOrder, SalesOrderItem


class SalesOrderListView(ListView):
    model = SalesOrder


class SalesOrderDetailView(StateChangeMixin, DetailView):
    model = SalesOrder

    def confirm(self):
        is_done, msg = StockOperate(self.request, self.object, self.object.items.all()).reserve_stock()
        return is_done, msg


class SalesOrderEditMixin(OrderFormInitialEntryMixin):
    model = SalesOrder
    form_class = SalesOrderForm
    template_name = 'form.html'


class SalesOrderCreateView(SalesOrderEditMixin, CreateView):
    pass


class SalesOrderUpdateView(SalesOrderEditMixin, UpdateView):
    pass


class SalesOrderItemEditView(OrderItemEditMixin):
    model = SalesOrderItem
    form_class = SalesOrderItemForm


class SalesOrderItemDeleteView(OrderItemDeleteMixin):
    model = SalesOrderItem


class SalesOrderQuickCreateView(SalesOrderEditMixin, CreateView):
    template_name = 'sales/form.html'

    def get_formset(self, extra=0):
        return inlineformset_factory(SalesOrder, SalesOrderItem, form=SalesOrderItemQuickForm, extra=extra)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = Cart(self.request)
        select_list = self.request.GET.getlist('select_product')
        select_items = [c for c in cart if str(c['product'].id) in select_list]
        if self.request.method == 'POST':
            formset = self.get_formset()(self.request.POST)
        else:
            formset = self.get_formset(extra=len(select_items))()
            for form, data in zip(formset.forms, select_items):
                initial = {'product': data['product'],
                           'piece': data['piece'],
                           'quantity': Decimal(data['quantity']),
                           'uom': data['product'].uom,
                           'location': int(data['location_id']),
                           'slab_id_list': ",".join(data['slab_id_list']),
                           }
                form.initial = initial
            # context['formset_display'] = zip(formset, select_items)
        context['formset'] = formset
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        with transaction.atomic():
            self.object = form.save()
            if formset.is_valid():
                formset.instance = self.object
                formset_data = formset.save(commit=False)
                cart = Cart(self.request)
                for f in formset_data:
                    cart.remove(f.product.id)
                    f.save()
        return super().form_valid(form)
