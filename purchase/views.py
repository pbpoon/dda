from django.db.models import Q
from django.shortcuts import redirect
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView, BaseDeleteView

from public.views import OrderItemEditMixin, StateChangeMixin, OrderItemDeleteMixin, OrderFormInitialEntryMixin, \
    FilterListView, ModalOptionsMixin
from purchase.filters import PurchaseOrderFilter
from .forms import PurchaseOrderItemForm, PurchaseOrderForm
from .models import PurchaseOrder, PurchaseOrderItem
from invoice.models import CreateInvoice

from django.contrib import messages


class PurchaseOrderListView(FilterListView):
    model = PurchaseOrder
    filter_class = PurchaseOrderFilter


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


class PurchaseOrderInvoiceOptionsEditView(ModalOptionsMixin):
    model = PurchaseOrder

    def get_options(self):
        if self.object.can_make_invoice_amount == 0:
            choices = [('do_nothing', '没有可开项')]
        else:
            # 如果有已经确认的出货单，就把可开的出货单列出
            in_out_orders = self.object.in_out_order.filter(Q(state='confirm') | Q(state='done'))
            choices = [('do_all', '{}'.format(
                '按全部订单行' if not in_out_orders else '按剩余可开项/金额:{}'.format(self.object.can_make_invoice_amount)))]
            choices.extend(
                [('do_' + str(order.pk), '收货单：{}:金额{:.2f}'.format(order.order, order.get_products_amount())) for order
                 in
                 in_out_orders if not order.has_from_order_invoice])
        return choices

    def do_option(self, option):
        _, order_str = option.split('_')
        if order_str == 'nothing':
            return False, '没有可开账单项'
        try:
            int(order_str)
            in_out_order = self.object.in_out_order.filter(pk=order_str)
            if in_out_order:
                order = in_out_order[0]
                invoice = order.make_from_order_invoice()
                comment = "按收货单 <a href='%s'>%s</a>,创建账单<a href='%s'>%s</a><br>" % (order.get_absolute_url(), order,
                                                                                    invoice.get_absolute_url(),
                                                                                    invoice)
                self.object.create_comment(**{'comment': comment})
                return True, '已按收货单{}创建账单:{}'.format(order.order, invoice.order)
        except Exception as e:
            if order_str == 'all':
                invoice = self.object.make_invoice()
                comment = "创建账单<a href='%s'>%s</a><br>" % (
                    invoice.get_absolute_url(), invoice)
                self.object.create_comment(**{'comment': comment})
                return True, '已创建账单:{}'.format(invoice.order)
        return False, '错误'
