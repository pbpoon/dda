from _decimal import Decimal
import itertools
import weasyprint
from django.db import transaction
from django.db.models import Q
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from cart.cart import Cart
from invoice.models import CreateInvoice
from public.stock_operate import StockOperate
from public.views import OrderFormInitialEntryMixin, OrderItemEditMixin, OrderItemDeleteMixin, StateChangeMixin, \
    ModalOptionsMixin, FilterListView
from sales.forms import SalesOrderForm, SalesOrderItemForm, SalesOrderItemQuickForm
from sales.models import SalesOrder, SalesOrderItem, Customer
from stone import settings
from .filters import SalesOrderFilter, CustomerFilter


class SalesOrderListView(FilterListView):
    model = SalesOrder
    filter_class = SalesOrderFilter
    paginate_by = 10


class SalesOrderDetailView(StateChangeMixin, DetailView):
    model = SalesOrder

    def get_btn_visible(self, state):
        return {'draft': {'cancel': True, 'confirm': True},
                'confirm': {'draft': True},
                'cancel': {'draft': True},
                'done': {}}[state]

    def confirm(self):
        return self.object.confirm()

    def draft(self):
        return self.object.draft()

    def cancel(self):
        return self.object.cancel()


class SalesOrderInvoiceOptionsEditView(ModalOptionsMixin):
    model = SalesOrder

    def get_options(self):
        if self.object.can_make_invoice_amount == 0:
            return [('do_nothing', '没有可开项')]
        # 如果有已经确认的出货单，就把可开的出货单列出
        in_out_orders = self.object.in_out_order.filter(Q(state='confirm') | Q(state='done'))
        choices = [('do_all', '{}'.format(
            '按全部订单行' if not in_out_orders else '按剩余可开项/金额:{}'.format(self.object.can_make_invoice_amount)))]
        choices.extend(
            [('do_' + str(order.pk), '提货单：{}:金额{:.2f}'.format(order.order, order.get_products_amount())) for order in
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
                comment = "按出货单 <a href='%s'>%s</a>,创建账单<a href='%s'>%s</a><br>" % (order.get_absolute_url(), order,
                                                                                    invoice.get_absolute_url(),
                                                                                    invoice)
                self.object.create_comment(**{'comment': comment})
                return True, '已按提货单{}创建账单:{}'.format(order.order, invoice.order)
        except Exception as e:
            invoice = self.object.make_invoice()
            comment = "创建账单<a href='%s'>%s</a><br>" % (
                invoice.get_absolute_url(), invoice)
            self.object.create_comment(**{'comment': comment})
            return True, '已创建账单:{}'.format(invoice.order)
        return False, '错误'


class SalesOrderEditMixin(OrderFormInitialEntryMixin):
    model = SalesOrder
    form_class = SalesOrderForm
    template_name = 'sales/form.html'


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
        return inlineformset_factory(SalesOrder, SalesOrderItem, form=SalesOrderItemQuickForm, extra=extra,
                                     can_delete=False)

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
                formset_data = formset.save()
                cart = Cart(self.request)
                for f in formset_data:
                    cart.remove(f.product.id)
        return HttpResponseRedirect(self.get_success_url())


def admin_order_pdf(request, order_id):
    order = get_object_or_404(SalesOrder, id=order_id)
    html = render_to_string('sales/salesorder_pdf.html', {'object': order})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="order_{}"'.format(order.id)
    weasyprint.HTML(string=html).write_pdf(response,
                                           stylesheets=[weasyprint.CSS(settings.STATIC_ROOT + '/css/materialize.css')])
    return response


class CustomerListView(FilterListView):
    model = Customer
    filter_class = CustomerFilter
    paginate_by = 10
