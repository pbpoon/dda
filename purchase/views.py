from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView, BaseDeleteView

from public.views import OrderItemEditMixin, StateChangeMixin, OrderItemDeleteMixin, OrderFormInitialEntryMixin
from .forms import PurchaseOrderItemForm, PurchaseOrderForm
from .models import PurchaseOrder, PurchaseOrderItem
from invoice.models import CreateInvoice

from django.contrib import messages


class PurchaseOrderListView(ListView):
    model = PurchaseOrder
    # template_name = 'purchase/order/list.html'
    paginate_by = 10


class PurchaseOrderDetailView(StateChangeMixin, DetailView):
    model = PurchaseOrder
    template_name = 'purchase/order/detail.html'

    def confirm(self):
        # map(lambda x: x.confirm(), self.object.items.all())
        return self.object.confirm()

    def draft(self):
        return self.object.draft()

    def make_invoice(self):
        items_dict_lst = [{'item': str(item.product), 'price': item.price, 'quantity': item.get_quantity()} for item in
                          self.object.items.all()]
        CreateInvoice(order=self.object, partner=self.object.partner, items_dict=items_dict_lst).make()
        return True


class PurchaseOrderEditMixin(OrderFormInitialEntryMixin):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'form.html'


class PurchaseOrderCreateView(PurchaseOrderEditMixin, CreateView):
    pass


class PurchaseOrderUpdateView(PurchaseOrderEditMixin, UpdateView):
    pass


class PurchaseOrderItemEditView(OrderItemEditMixin):
    form_class = PurchaseOrderItemForm
    model = PurchaseOrderItem


class PurchaseOrderItemDeleteView(OrderItemDeleteMixin):
    model = PurchaseOrderItem
