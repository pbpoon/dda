from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from public.views import OrderFormInitialEntryMixin, OrderItemEditMixin, OrderItemDeleteMixin
from sales.forms import SalesOrderForm, SalesOrderItemForm
from sales.models import SalesOrder, SalesOrderItem


class SalesOrderListView(ListView):
    model = SalesOrder


class SalesOrderDetailView(DetailView):
    model = SalesOrder


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
