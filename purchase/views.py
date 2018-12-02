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
    template_name = 'purchase/order/list.html'
    paginate_by = 10


class PurchaseOrderDetailView(StateChangeMixin, DetailView):
    model = PurchaseOrder
    template_name = 'purchase/order/detail.html'

    def confirm(self):
        products = (item.product for item in self.object.items.all())
        for p in products:
            p.activate = True
            p.save()
        obj = self.get_object()
        comment = '{}状态 =>'.format(obj.state)
        obj.state = 'confirm'
        obj.save()
        # 日后生产invoice
        comment += obj.state
        obj.comments.create(user=self.request.user, comment=comment)

        items_dict_lst = [{'item': str(item.product), 'price': item.price, 'quantity': item.get_quantity()} for item in
                          obj.items.all()]
        CreateInvoice(order=obj, partner=obj.partner, entry=obj.entry, items_dict_lst=items_dict_lst)
        msg = '设置订单{}设置成 确认 状态'.format(obj.order)
        return True, msg

    def draft(self):
        obj = self.get_object()
        obj.state = 'draft'
        obj.save()
        messages.info(self.request, '设置订单{}设置成 草稿 状态'.format(obj.order))
        return super(PurchaseOrderDetailView, self).draft()


class PurchaseOrderEditMixin(OrderFormInitialEntryMixin):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    # fields = ('date', 'partner', 'handler', 'currency', 'uom')
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
