from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView, BaseDeleteView

from public.views import OrderItemEditMixin, StateChangeMixin, OrderItemDeleteMixin
from .forms import PurchaseOrderItemForm, PurchaseOrderForm
from django.contrib.auth.mixins import LoginRequiredMixin
from product.models import Product
from .models import PurchaseOrder, PurchaseOrderItem
from invoice.models import CreateInvoice

from django.contrib import messages


class GetItemsMixin:
    def get_context_data(self, **kwargs):
        if self.object:
            items = self.object.items.all()
            kwargs.update({'object_list': items})
        return super(GetItemsMixin, self).get_context_data(**kwargs)


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
        messages.info(self.request, '设置订单{}设置成 确认 状态'.format(obj.order))
        return super(PurchaseOrderDetailView, self).confirm()

    def draft(self):
        obj = self.get_object()
        obj.state = 'draft'
        obj.save()
        messages.info(self.request, '设置订单{}设置成 草稿 状态'.format(obj.order))
        return super(PurchaseOrderDetailView, self).draft()


class PurchaseOrderCreateView(CreateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    # fields = ('date', 'partner', 'handler', 'currency', 'uom')
    template_name = 'purchase/order/form.html'

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.entry = self.request.user
        instance.save()
        return super(PurchaseOrderCreateView, self).form_valid(form)


class PurchaseOrderItemEditView(OrderItemEditMixin):
    form_class = PurchaseOrderItemForm
    model = PurchaseOrderItem


class PurchaseOrderItemDeleteView(OrderItemDeleteMixin):
    model = PurchaseOrderItem
