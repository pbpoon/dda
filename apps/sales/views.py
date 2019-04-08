import collections
from _decimal import Decimal
import weasyprint
from datetime import datetime, timedelta
from django.core import signing
from django.db import transaction
from django.db.models import Q, Sum, F
from django.db.models.functions import TruncMonth
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, render_to_response
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import DetailView, CreateView, UpdateView, DeleteView
from django.views.generic.detail import BaseDetailView
from django.views.generic.edit import BaseDeleteView
from django.views.generic.dates import MonthArchiveView, BaseYearArchiveView, YearArchiveView
from django.contrib import messages

from cart.cart import Cart
from public.permissions_mixin_views import ViewPermissionRequiredMixin, PostPermissionRequiredMixin, \
    DynamicPermissionRequiredMixin
from public.views import OrderFormInitialEntryMixin, OrderItemEditMixin, OrderItemDeleteMixin, StateChangeMixin, \
    ModalOptionsMixin, FilterListView
from action.wechat import SentWxMsgMixin, WxJsSdkMixin
from sales.forms import SalesOrderForm, SalesOrderItemForm, SalesOrderItemQuickForm, CustomerForm, \
    SalesOrderCreateByCustomerForm, SalesLeadsForm, SalesLeadsDetailForm
from sales.models import SalesOrder, SalesOrderItem, Customer, SalesLeads
from django.conf import settings
from .filters import SalesOrderFilter, CustomerFilter
from wkhtmltopdf.views import PDFTemplateView
from .models.leads import SALES_LEADS_STATE_CHOICES, MISS_REASON_CHOICES


class SalesOrderListView(FilterListView):
    model = SalesOrder
    filter_class = SalesOrderFilter


class SalesOrderDelayListView(SalesOrderListView):
    ordering = ('date', 'created')
    template_name = 'sales/salesorder_delay_list.html'

    def get_queryset(self):
        qs = super().get_queryset()
        ten_days_ago = datetime.now() - timedelta(days=10)
        return qs.annotate(delay=datetime.now() - F('date')).filter(date__lte=ten_days_ago,
                                                                    state='confirm')


class UserSalesOrderListView(SalesOrderListView):

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(handler=self.request.user)


class SalesOrderMonthListView(ViewPermissionRequiredMixin, MonthArchiveView):
    model = SalesOrder
    date_field = 'date'
    month_format = '%m'

    # year_format = '%Y'
    # template_name = 'sales/salesorder_archive_month.html'

    def get_charts_data(self, object_list):
        data = collections.OrderedDict()
        thick = collections.defaultdict(lambda: 0)
        for obj in object_list.filter(state__in=('confirm', 'done')).order_by('date'):
            state = obj.get_state_display()
            if state not in data:
                d = collections.defaultdict(lambda: 0)
                data[state] = d
            data[state]['quantity'] += int(obj.quantity)
            for item in obj.items.all():
                thickness = item.product.thickness if item.product.type == 'slab' else '荒料'
                thick[thickness] += int(item.quantity)
        series = [{'name': '状态占比',
                   'data': [{'name': str(state), 'y': data[state]['quantity']} for state in data]}]
        series2 = [{'name': '规格占比',
                    'data': [{'name': str(thickness), 'y': thick[thickness]} for thickness in thick]}]

        data = {'series': series,
                'series2': series2}
        return data

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        object_list = context.get('object_list')
        data = self.get_charts_data(object_list)
        context.update(data)
        context['title'] = '%s月销量' % context['month']
        return context


class SalesOrderChrtsView(ViewPermissionRequiredMixin, YearArchiveView):
    model = SalesOrder
    date_field = 'date'
    year_format = '%Y'
    make_object_list = True
    template_name = 'sales/salesorder_chart.html'

    def get_charts_data(self, object_list):
        data = collections.OrderedDict()
        for obj in object_list.filter(state__in=('confirm', 'done')).order_by('date'):
            month = obj.date.strftime("%Y-%m")
            if month not in data:
                d = collections.defaultdict(lambda: 0)
                data[month] = d
            data[month]['quantity'] += int(obj.quantity)
            if obj.state == 'confirm':
                data[month]['confirm_quantity'] += int(obj.quantity)
                data[month]['confirm_amount'] += int(obj.amount)
            elif obj.state == 'done':
                data[month]['done_quantity'] += int(obj.quantity)
                data[month]['done_amount'] += int(obj.amount)
            for item in obj.items.all():
                thickness = item.product.thickness if item.product.type == 'slab' else '荒料'
                data[month][thickness] += int(item.quantity)
        categories = [str(i) for i in data.keys()]
        quantity = {'type': 'line', 'name': '总数量',
                    'data': [data[month]['quantity'] for month in data]}
        confirm_quantity = {'type': 'line', 'name': '确认数量',
                            'data': [data[month]['confirm_quantity'] for month in data]}
        confirm_amount = {'type': 'column', 'yAxis': 1, 'name': '确认金额',
                          'data': [data[month]['confirm_amount'] for month in data]}
        done_quantity = {'type': 'line', 'name': '完成数量',
                         'data': [data[month]['done_quantity'] for month in data]}
        done_amount = {'type': 'column', 'yAxis': 1, 'name': '完成金额',
                       'data': [data[month]['done_amount'] for month in data]}
        thickness_names = {thickness for month in data for thickness in data[month] if
                           thickness not in (
                               'quantity', 'confirm_quantity', 'confirm_amount', 'done_quantity', 'done_amount')}
        series2 = []
        for thickness in thickness_names:
            _lst = []
            for month in data:
                i = data[month][thickness] or 0
                _lst.append(i)
            d = {'type': 'line', 'name': str(thickness),
                 'data': _lst}
            series2.append(d)
        series2 = sorted(series2, key=lambda x: x['name'])
        series = [confirm_amount, done_amount, quantity, confirm_quantity, done_quantity]
        data = {'series': series, 'categories': categories,
                'series2': series2}
        return data

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        object_list = context.get('object_list')
        data = self.get_charts_data(object_list)
        context.update(data)
        context['title'] = '%s年销量' % context['year']
        return context


class SalesSentWxMsg(SentWxMsgMixin):
    app_name = 'zdzq_main'
    user_ids = '@all'

    # SECRET = 'la8maluNMN_imtic0Jp0ECmE71ca2iQ80n3-a8HFFv4'

    def get_js_sdk_url(self):
        return self.request.build_absolute_uri(self.object.get_absolute_url())

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

    def get_js_sdk_title(self):
        return f'{self.object._meta.verbose_name}/{self.object}'

    def get_js_sdk_desc(self):
        return f'{self.object.partner}/{self.object.get_address()}'


class SalesOrderDetailView(StateChangeMixin, SalesSentWxMsg, DetailView):
    model = SalesOrder

    def get_btn_visible(self, state):
        return {'draft': {'cancel': True, 'confirm': True},
                'confirm': {'draft': True},
                'cancel': {'draft': True, },
                'done': {}}[state]

    def get_js_sdk_link(self):
        from django.conf import settings
        data = {'pk': self.object.id}
        string = signing.dumps(data)
        path = reverse('sales_order_pdf_share', args=[string])
        return f"{settings.DEFAULT_DOMAIN}{path}"

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


class OrderToPdfViewMixin(BaseDetailView, PDFTemplateView):
    show_content_in_browser = True
    model = SalesOrder
    header_template = 'sales/pdf/header.html'
    template_name = 'sales/pdf/salesorder_pdf.html'
    footer_template = 'sales/pdf/footer.html'

    # cmd_options = {
    # 'page-height': '19cm',
    # 'page-width': '13cm',
    # 'margin-top': '0',
    # 'margin-left': '0',
    # 'margin-bottom': '0',
    # 'margin-right': '0',
    # }

    def get_filename(self):
        self.object = self.get_object()
        return '%s.pdf' % self.object.order

    def get_context_data(self, **kwargs):
        from public.gen_barcode import GenBarcode
        path = reverse('sales_order_detail', args=[self.object.id])
        kwargs['link'] = f"{settings.DEFAULT_DOMAIN}{path}"
        kwargs['show_account'] = True
        kwargs['barcode'] = GenBarcode(self.object.order, barcode_type='code39').value
        content = self.response_class
        return super().get_context_data(**kwargs)


class OrderToPdfView(ViewPermissionRequiredMixin, OrderToPdfViewMixin):
    pass


class SalesOrderPdfShareDisplayView(OrderToPdfViewMixin):

    def get_object(self, queryset=None):
        return self.object

    def dispatch(self, request, *args, **kwargs):
        string = kwargs.get('string')
        if string:
            try:
                data = signing.loads(string)
                self.object = get_object_or_404(self.model, pk=data['pk'])
                kwargs.update(data)
                return super().dispatch(request, *args, **kwargs)
            except Exception as e:
                print(e)
        return render_to_response("404.html", {})


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


class CustomerCreateModalView(CustomerEditMixin, CreateView):
    template_name = 'sales/modal_form.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.province = form.cleaned_data.get('partner_province')
        self.object.save()
        partner_id = self.object.id
        partner_text = '%s:%s:%s' % (self.object, self.object.get_address(), self.object.phone)
        province_id = self.object.province.code
        province_text = str(self.object.province)
        city_id = self.object.city.id
        city_text = str(self.object.city)
        return JsonResponse({'state': 'ok',
                             'partner_id': partner_id,
                             'partner_text': partner_text,
                             'province_id': province_id,
                             'province_text': province_text,
                             'city_id': city_id,
                             'city_text': city_text,
                             })


class CustomerUpdateView(CustomerEditMixin, UpdateView):
    pass


class SalesOrderCreateByCustomerView(SalesOrderCreateView):
    form_class = SalesOrderCreateByCustomerForm

    def get_initial(self):
        initial = super().get_initial()
        initial['partner'] = self.kwargs['customer_id']
        return initial


class SalesLeadsListView(FilterListView):
    model = SalesLeads


class SalesLeadsDetailView(DetailView):
    model = SalesLeads


class SalesLeadsEditMixin(OrderFormInitialEntryMixin):
    model = SalesLeads
    form_class = SalesLeadsForm
    detail_form_class = SalesLeadsDetailForm
    template_name = 'sales/form.html'

    def get_prefix(self):
        return 'main'

    def get_context_data(self, **kwargs):
        if self.request.method == 'POST':
            kwargs['detail_form'] = self.detail_form_class(self.request.POST, self.request.FILES, prefix='detail_form')
        else:
            detail_initial = {}
            if self.object:
                detail_initial = {
                    'start_time': self.object.start_time,
                    'due_time': self.object.due_time,
                    'category': self.object.category,
                    'type': self.object.type,
                    'thickness': self.object.thickness,
                    'quantity': self.object.quantity,
                    'long_lt': self.object.long_lt,
                    'long_gt': self.object.long_gt,
                    'height_lt': self.object.height_lt,
                    'height_gt': self.object.height_gt,
                }
            kwargs['detail_form'] = self.detail_form_class(prefix='detail_form', initial=detail_initial)
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        if not kwargs.get('pk'):
            self.object = None
        else:
            self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        form = context['form']
        detail_form = context['detail_form']
        if form.is_valid() and detail_form.is_valid():
            self.object = form.save(commit=False)
            cd = detail_form.cleaned_data
            self.object.start_time = cd.get('start_time', None)
            self.object.due_time = cd.get('due_time', None)
            self.object.type = cd.get('type', None)
            self.object.thickness = cd.get('thickness', None)
            self.object.quantity = cd.get('quantity', None)
            self.object.long_lt = cd.get('long_lt', None)
            self.object.long_gt = cd.get('long_gt', None)
            self.object.price_lt = cd.get('price_lt', None)
            self.object.price_gt = cd.get('price_gt', None)
            self.object.height_lt = cd.get('height_lt', None)
            self.object.height_gt = cd.get('height_gt', None)
            self.object.save()
            form.save_m2m()
            return HttpResponseRedirect(self.get_success_url())
        return render(self.request, self.template_name, context)


class SalesLeadsCreateView(SalesLeadsEditMixin, CreateView):
    pass


class SalesLeadsUpdateView(SalesLeadsEditMixin, UpdateView):
    pass


class SalesLeadsStateChangeView(ModalOptionsMixin):
    model = SalesLeads

    def get_initial(self):
        initial = {'options': self.object.state}
        return initial

    def get_options(self):
        return ((i[0], f"{i[1]}({i[0]})") for i in SALES_LEADS_STATE_CHOICES[1:-1])

    def get_content(self):
        return '把 线索 状态推进到：'

    def do_option(self, option):
        self.object.state = option
        self.object.save()
        return True, '已把状态 推进到 %s' % dict(SALES_LEADS_STATE_CHOICES)[option]


class SalesLeadsMissView(ModalOptionsMixin):
    model = SalesLeads

    def get_options(self):
        return MISS_REASON_CHOICES

    def do_option(self, option):
        self.object.miss_reason = option
        self.object.state = '0%'
        self.object.save()
        return True, '虽然错失了这次， 继续努力！'

    def get_content(self):
        return '错失的原因为:'


class SalesLeadsWinView(ModalOptionsMixin):
    model = SalesLeads

    def get_options(self):
        return (('do_yes', '是'), ('do_no', '否'))

    def get_content(self):
        return '恭喜！赢得订单？'

    def do_yes(self):
        self.object.state = '100%'
        # 发sent_wx
        self.object.save()
        return True, '恭喜！再下一城。'

    def do_no(self):
        return True, '再努力一下！'
