from _decimal import Decimal
import weasyprint
from datetime import datetime
from django.db import transaction
from django.db.models import Q
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, CreateView, UpdateView, DeleteView
from django.views.generic.detail import BaseDetailView
from django.views.generic.edit import BaseDeleteView
from django.contrib import messages

from cart.cart import Cart
from public.permissions_mixin_views import ViewPermissionRequiredMixin, PostPermissionRequiredMixin, \
    DynamicPermissionRequiredMixin
from public.views import OrderFormInitialEntryMixin, OrderItemEditMixin, OrderItemDeleteMixin, StateChangeMixin, \
    ModalOptionsMixin, FilterListView, SentWxMsgMixin
from sales.forms import SalesOrderForm, SalesOrderItemForm, SalesOrderItemQuickForm, CustomerForm, \
    SalesOrderCreateByCustomerForm
from sales.models import SalesOrder, SalesOrderItem, Customer
from django.conf import settings
from .filters import SalesOrderFilter, CustomerFilter
from wkhtmltopdf.views import PDFTemplateView


class SalesOrderListView(FilterListView):
    model = SalesOrder
    filter_class = SalesOrderFilter
    paginate_by = 10


class SalesSentWxMsg(SentWxMsgMixin):
    app_name = 'zdzq_main'
    user_ids = '@all'

    # SECRET = 'la8maluNMN_imtic0Jp0ECmE71ca2iQ80n3-a8HFFv4'

    def get_url(self):
        return "%s" % (self.request.build_absolute_uri())

    def get_title(self):
        title = "%s/金额：¥%s    [%s]" % (
            self.model._meta.verbose_name, self.object.amount, self.object.get_state_display())
        return title

    def get_items(self):
        html = '\n---------------------------------'
        for item in self.object.items.all():
            if html:
                html += '\n'
            html += '(%s) %s /%s夹/%s件/%s%s *¥%s' % (
                item.line, item.product, str(item.package_list.get_part()) if item.package_list else '',
                item.piece, item.quantity, item.uom, item.price)
        html += '\n---------------------------------\n'
        html += '合计：'
        print('item html', html)
        for key, item in self.object.get_total().items():
            html += '%s:%s %s件/%s%s\n' % (
                key, item['part'] if item.get('part') else '', item['piece'],
                item['quantity'], item['uom'])
        html += '\n金额：¥ %s' % self.object.amount
        return html

    def get_description(self):
        html = '单号:%s\n' % self.object.order
        html += '\n客户:%s' % self.object.partner
        html += '\n销往:%s' % self.object.get_address()
        html += "\n订单日期:%s" % (datetime.strftime(self.object.date, "%Y/%m/%d"))
        html += "\n销售:%s" % self.object.handler
        now = datetime.now()
        html += '%s' % self.get_items()
        html += '\n操作:%s \n@%s' % (self.request.user, datetime.strftime(now, '%Y/%m/%d %H:%M'))
        return html


class SalesOrderDetailView(StateChangeMixin, SalesSentWxMsg, DetailView):
    model = SalesOrder

    def get_btn_visible(self, state):
        return {'draft': {'cancel': True, 'confirm': True},
                'confirm': {'draft': True},
                'cancel': {'draft': True, },
                'done': {}}[state]

    def confirm(self):
        is_done, msg = self.object.confirm()
        if is_done:
            self.sent_msg()
        return is_done, msg

    def draft(self):
        is_done, msg = self.object.draft()
        if is_done:
            self.sent_msg()
        return is_done, msg

    def cancel(self):
        is_done, msg = self.object.cancel()
        if is_done:
            self.sent_msg()
        return is_done, msg

    def done(self):
        is_done, msg = self.object.done()
        if is_done:
            self.sent_msg()
        return True, ''


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


class SalesOrderDeleteView(PostPermissionRequiredMixin, BaseDeleteView):
    model = SalesOrder
    model_permission = ['delete']

    def get_success_url(self):
        return reverse_lazy('sales_order_list')


class SalesOrderEditMixin(OrderFormInitialEntryMixin, DynamicPermissionRequiredMixin):
    model_permission = ('add', 'change')
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


def admin_order_pdf(request, pk):
    order = get_object_or_404(SalesOrder, id=pk)
    html = render_to_string('sales/salesorder_pdf.html', {'object': order})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="order_{}"'.format(order.id)
    weasyprint.HTML(string=html).write_pdf(response,
                                           stylesheets=[weasyprint.CSS(settings.STATIC_ROOT + '/css/materialize.css')])
    return response


class OrderToPdfView(BaseDetailView, PDFTemplateView):
    show_content_in_browser = True
    model = SalesOrder
    header_template = 'sales/pdf/header.html'
    template_name = 'sales/pdf/salesorder_pdf.html'
    footer_template = 'sales/pdf/footer.html'

    # cmd_options = {
    #     'page-height': '19cm',
    #     'page-width': '13cm',
    #     'margin-top': '0',
    # 'margin-left': '0',
    # 'margin-bottom': '0',
    # 'margin-right': '0',
    # }

    def get_filename(self):
        self.object = self.get_object()
        return '%s.pdf' % self.object.order

    def get_context_data(self, **kwargs):
        from public.gen_barcode import GenBarcode
        kwargs['show_account'] = True
        kwargs['barcode'] = GenBarcode(self.object.order, barcode_type='code39').value
        return super().get_context_data(**kwargs)


class CustomerListView(FilterListView):
    model = Customer
    filter_class = CustomerFilter
    paginate_by = 10
    template_name = 'sales/customer_list.html'


class CustomerDetailView(DetailView):
    model = Customer
    template_name = 'sales/customer_detail.html'


class CustomerDeleteView(ViewPermissionRequiredMixin, BaseDeleteView):
    model = Customer

    def get_success_url(self):
        return reverse_lazy('customer_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.sales_order.all():
            messages.error(request, '该客户名下有订单记录，不能删去')
            return HttpResponseRedirect(self.object.get_absolute_url())
            # return self.get(request, *args, **kwargs)
        return super().delete(request, *args, **kwargs)


class CustomerEditMixin:
    model = Customer
    form_class = CustomerForm
    template_name = 'sales/form.html'

    def get_initial(self):
        initial = super().get_initial()
        initial['entry'] = self.request.user.id
        return initial


class CustomerCreateView(CustomerEditMixin, CreateView):
    pass


class CustomerUpdateView(CustomerEditMixin, UpdateView):
    pass


class SalesOrderCreateByCustomerView(SalesOrderCreateView):
    form_class = SalesOrderCreateByCustomerForm

    def get_initial(self):
        initial = super().get_initial()
        initial['partner'] = self.kwargs['customer_id']
        return initial
