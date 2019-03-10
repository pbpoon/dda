import time

from datetime import datetime
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView
from django.views.generic.detail import BaseDetailView
from django.views.generic.edit import ModelFormMixin, CreateView, UpdateView, BaseDeleteView
from django.contrib import messages
from django.views.generic.list import MultipleObjectMixin
from wkhtmltopdf.views import PDFTemplateView

from invoice.models import CreateInvoice
from mrp.filters import InOutOrderFilter, MoveLocationOrderFilter, ProductionOrderFilter, InventoryOrderFilter, \
    ProductFilter
from mrp.models import ProductionOrder, ProductionOrderRawItem, ProductionOrderProduceItem, ProductionType, InOutOrder, \
    InOutOrderItem, Expenses, ExpensesItem, InventoryOrder, InventoryOrderItem, InventoryOrderNewItem, MrpSupplier
from mrp.models import TurnBackOrder, TurnBackOrderItem
from partner.models import Partner

from product.models import PackageList
from public.permissions_mixin_views import ViewPermissionRequiredMixin, DynamicPermissionRequiredMixin
from public.utils import Package, StockOperateItem
from public.views import OrderItemEditMixin, OrderItemDeleteMixin, OrderFormInitialEntryMixin, FilterListView, \
    SentWxMsgMixin
from public.widgets import SwitchesWidget
from purchase.models import PurchaseOrder
from public.views import GetItemsMixin, StateChangeMixin
from public.stock_operate import StockOperate
from sales.models import SalesOrder
from stock.models import Stock, Location
from .models import MoveLocationOrder, MoveLocationOrderItem
from .forms import MoveLocationOrderItemForm, MoveLocationOrderForm, ProductionOrderForm, \
    ProductionOrderRawItemForm, ProductionOrderProduceItemForm, InOutOrderForm, MrpItemExpensesForm, TurnBackOrderForm, \
    TurnBackOrderItemForm, InventoryOrderForm, InventoryOrderItemForm, InventoryOrderNewItemForm, SupplierForm


class ChangeStateSentWx(SentWxMsgMixin):
    app_name = 'zdzq_main'

    def get_title(self):
        title = "%s[销售提货]    [%s]" % (
            self.object.order, self.object.get_state_display())
        return title

    def get_items(self):
        html = '\n---------------------------------'
        for item in self.object.items.all():
            if html:
                html += '\n'
            html += '(%s) %s /%s夹/%s件/%s%s' % (
                item.line, item.product, str(item.package_list.get_part()) if item.package_list else '',
                item.piece, item.quantity, item.uom)
        html += '\n---------------------------------\n'
        html += '合计：'
        print('item html', html)
        for key, item in self.object.get_total().items():
            html += '%s:%s %s件/%s%s\n' % (
                key, item['part'] if item.get('part') else '', item['piece'],
                item['quantity'], item['uom'])
        return html

    def get_description(self):
        html = '单号:%s\n' % self.object.from_order.order
        html += '\n--%s--\n' % self.object.from_order.progress
        html += '\n客户:%s' % self.object.from_order.partner
        html += '\n销往:%s' % self.object.from_order.get_address()
        html += "\n订单日期:%s" % (datetime.strftime(self.object.date, "%Y/%m/%d"))
        html += "\n经办人:%s" % self.object.from_order.handler
        now = datetime.now()
        html += '%s' % self.get_items()
        html += '\n操作:%s \n@%s' % (self.request.user, datetime.strftime(now, '%Y/%m/%d %H:%M'))
        return html


class MoveLocationOrderListView(FilterListView):
    model = MoveLocationOrder
    filter_class = MoveLocationOrderFilter


class MoveLocationOrderDetailView(StateChangeMixin, GetItemsMixin, DetailView):
    model = MoveLocationOrder

    def get_btn_visible(self, state):
        return {'draft': {'done': True, 'confirm': True, 'cancel': True},
                'confirm': {'done': True, 'draft': True},
                'done': {'turn_back': True},
                'cancel': {'delete': True}
                }[state]

    def done(self):
        return self.object.done()

    def confirm(self):
        return self.object.confirm()

    def draft(self):
        return self.object.draft()

    def cancel(self):
        return self.object.cancel()


class MoveLocationOrderDeleteView(BaseDeleteView):
    model = MoveLocationOrder

    def get_success_url(self):
        return reverse_lazy('move_location_order_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.state in ('cancel', 'draft'):
            messages.success(self.request, '已成功删除该订单')
            return super().delete(self.request, *args, **kwargs)
        messages.error(self.request, '不能删除该订单')
        return HttpResponseRedirect(reverse_lazy(self.object.get_absolute_url()))


class MoveLocationOrderEditMixin(OrderFormInitialEntryMixin):
    model = MoveLocationOrder
    form_class = MoveLocationOrderForm
    template_name = 'mrp/form.html'


class MoveLocationOrderCreateView(MoveLocationOrderEditMixin, CreateView):
    pass


class MoveLocationOrderUpdateView(MoveLocationOrderEditMixin, UpdateView):
    pass


class MoveLocationOrderItemEditView(OrderItemEditMixin):
    model = MoveLocationOrderItem
    form_class = MoveLocationOrderItemForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['move_order'] = self.order
        return kwargs


class MoveLocationOrderItemDeleteView(OrderItemDeleteMixin):
    model = MoveLocationOrderItem


class ProductionTypeListView(ListView):
    model = ProductionType


class ProductionTypeDetailView(DetailView):
    model = ProductionType


class ProductionTypeCreateView(CreateView):
    model = ProductionType
    fields = '__all__'
    template_name = 'mrp/form.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['activate'].widget = SwitchesWidget()
        return form


class ProductionTypeUpdateView(UpdateView):
    model = ProductionType
    fields = '__all__'
    template_name = 'mrp/form.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['activate'].widget = SwitchesWidget()
        return form


class ProductionOrderListView(FilterListView):
    model = ProductionOrder
    filter_class = ProductionOrderFilter


class ProductionOrderDetailView(StateChangeMixin, DetailView):
    model = ProductionOrder

    def get_btn_visible(self, state):
        return {'draft': {'done': True, 'cancel': True},
                'cancel': {},
                'done': {'turn_back': True}}[state]

    def done(self):
        return self.object.done()

    def cancel(self):
        return self.object.cancel()


class ProductionOrderEditMixin(OrderFormInitialEntryMixin):
    model = ProductionOrder
    form_class = ProductionOrderForm
    template_name = 'mrp/form.html'

    def get_initial(self):
        initial = super().get_initial()
        initial['handle'] = initial.get('entry')
        return initial


class ProductionOrderCreateView(ProductionOrderEditMixin, CreateView):
    pass


class ProductionOrderUpdateView(ProductionOrderEditMixin, UpdateView):
    pass


class ProductionOrderItemEditMixin(OrderItemEditMixin):
    item_id = None
    item_model = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['production_order'] = self.order
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        if kwargs.get('item_id'):
            self.item_id = kwargs.get('item_id')
        return super().dispatch(request, *args, **kwargs)


class ProductionOrderRawItemEditView(ProductionOrderItemEditMixin):
    model = ProductionOrderRawItem
    form_class = ProductionOrderRawItemForm

    def get_initial(self):
        initial = super().get_initial()
        initial['location'] = self.order.location.id
        return initial


class ProductionOrderRawItemDeleteView(OrderItemDeleteMixin):
    model = ProductionOrderRawItem
    item_model = ProductionOrderRawItem


class ProductionOrderProduceItemEditView(ProductionOrderItemEditMixin):
    model = ProductionOrderProduceItem
    form_class = ProductionOrderProduceItemForm
    item_model = ProductionOrderRawItem

    def get_initial(self):
        initial = super().get_initial()
        initial['raw_item'] = self.item_id if self.item_id else self.object.raw_item
        return initial


class ProductionOrderProduceItemDeleteView(OrderItemDeleteMixin):
    model = ProductionOrderProduceItem


class InOutOrderListView(FilterListView):
    model = InOutOrder
    filter_class = InOutOrderFilter


class InOutOrderDetailView(StateChangeMixin, ChangeStateSentWx, DetailView):
    model = InOutOrder

    def done(self):
        is_done, msg = self.object.done()
        if not is_done:
            print('error')
        if is_done:
            self.sent_msg()
        return True, ''

    def cancel(self):
        is_done, msg = self.object.cancel()
        if is_done:
            self.sent_msg()
        return True, ''

    def get_btn_visible(self, state):
        btn_visible = {}
        if state == 'draft':
            btn_visible.update({'done': True, 'delete': True})
        elif state == 'done':
            btn_visible.update({'turn_back': True})
        return btn_visible


class InOutOrderDeleteView(BaseDeleteView):
    model = InOutOrder

    def get_success_url(self):
        # return self.request.META.get('HTTP_REFERER')
        return self.object.from_order.get_absolute_url()


class InOutOrderEditView(OrderFormInitialEntryMixin):
    model = InOutOrder
    form_class = InOutOrderForm
    template_name = 'mrp/form.html'
    sales_order = None
    purchase_order = None

    def dispatch(self, request, *args, **kwargs):
        if kwargs.get('sales_order_id'):
            self.sales_order = get_object_or_404(SalesOrder, pk=kwargs.get('sales_order_id'))
        if kwargs.get('purchase_order_id'):
            self.purchase_order = get_object_or_404(PurchaseOrder, pk=kwargs.get('purchase_order_id'))
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        if self.sales_order:
            initial['sales_order'] = self.sales_order
            initial['partner'] = self.sales_order.partner
            initial['type'] = 'out'
        else:
            initial['purchase_order'] = self.purchase_order
            initial['partner'] = self.purchase_order.partner
            initial['type'] = 'in'
        return initial


class PurchaseOrderInOrderCreateView(InOutOrderEditView, CreateView):
    pass


class SalesOrderInOrderCreateView(InOutOrderEditView, CreateView):
    pass


class InOutOrderItemEditView(OrderItemEditMixin):
    model = InOutOrderItem


class InOutOrderItemDeleteView(OrderItemDeleteMixin):
    model = InOutOrderItem


class MrpItemExpenseEditView(ModelFormMixin, View):
    model = Expenses
    form_class = MrpItemExpensesForm
    template_name = 'item_form.html'
    item_model = None
    item = None

    def dispatch(self, request, item_model, item_id, pk=None):
        if pk:
            self.object = self.get_object()
        else:
            self.object = None
        self.item_model = apps.get_model(app_label='mrp', model_name=item_model)
        self.item = self.item_model.objects.get(pk=item_id)
        return super().dispatch(request, item_model, item_id, pk)

    def get_initial(self):
        initial = super().get_initial()
        initial['content_type'] = ContentType.objects.get_for_model(self.item_model)
        initial['object_id'] = self.item.id
        return initial

    def get(self, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return HttpResponse(render_to_string(self.template_name, context))

    def post(self, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        form = context['form']
        if form.is_valid():
            self.object = form.save()
            return JsonResponse({'state': 'ok'})
        return HttpResponse(render_to_string(self.template_name, context))


class MrpExpenseDeleteView(OrderItemDeleteMixin):
    model = Expenses


class MrpExpensesItemListView(FilterListView):
    model = ExpensesItem
    template_name = 'mrp/expenses/expenses_item_list.html'


class MrpExpenseItemEditMixin:
    model = ExpensesItem
    template_name = 'item_form.html'
    fields = '__all__'

    def form_valid(self, form):
        form.save()
        return JsonResponse({'state': 'ok'})


class MrpExpenseItemCreateView(MrpExpenseItemEditMixin, CreateView):
    pass


class MrpExpenseItemUpdateView(MrpExpenseItemEditMixin, UpdateView):
    pass


class TurnBackOrderDetailView(StateChangeMixin, DetailView):
    model = TurnBackOrder

    def get_btn_visible(self, state):
        btn_visible = {}
        if state == 'draft':
            btn_visible.update({'done': True, 'delete': True})
        return btn_visible

    def done(self):
        return self.object.done()


class TurnBackOrderDeleteView(BaseDeleteView):
    model = TurnBackOrder

    def get_success_url(self):
        return self.object.get_obj().get_absolute_url()


class TurnBackOrderEditMixin:
    model = TurnBackOrder
    form_class = TurnBackOrderForm
    template_name = 'form.html'
    from_order = None

    def get_model(self, model_name):
        return apps.get_model(app_label='mrp', model_name=model_name)

    def dispatch(self, request, model_name, from_order_id, pk=None):
        if pk:
            self.sales_order = get_object_or_404(self.model, pk=pk)
            self.object = self.get_object()
            self.from_order = self.object.from_order
        else:
            self.object = None
        if model_name and from_order_id:
            model = self.get_model(model_name)
            self.from_order = get_object_or_404(model, pk=from_order_id)
        return super().dispatch(request, model_name, from_order_id, pk=None)

    def get_initial(self):
        initial = super().get_initial()
        initial['content_type'] = ContentType.objects.get_for_model(self.from_order)
        initial['object_id'] = self.from_order.id
        initial['entry'] = self.request.user.id
        initial['handle'] = self.request.user.id
        return initial

    def get_items(self):
        # 如果是update状态，有object就返回items
        if self.object:
            items = self.object.items.all()
            if items:
                return items
        if self.from_order:
            items = self.from_order.items.all()
            if hasattr(self.from_order, 'produce_items'):
                items = list(items)
                items.extend(list(self.from_order.produce_items.all()))
            for item in items:
                fields_lst = {f.name for f in TurnBackOrderItem._meta.fields if f.name != 'id'}
                new_item = {f.name: getattr(item, f.name) for f in item._meta.fields if
                            f.name != 'id' and f.name in fields_lst}
                new_item['location'], new_item['location_dest'] = new_item['location_dest'], new_item['location']
                new_item['order'] = self.object
                new_item['package_list'] = new_item['package_list'].copy() if new_item.get('package_list') else None
                TurnBackOrderItem.objects.create(**new_item)

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()
            self.get_items()
            return super().form_valid(form)


class TurnBackOrderCreateView(TurnBackOrderEditMixin, CreateView):
    pass


class TurnBackOrderUpdateView(TurnBackOrderEditMixin, UpdateView):
    pass


class TurnBackOrderItemDeleteView(OrderItemDeleteMixin):
    model = TurnBackOrderItem


class TurnBackOrderItemEditMixin:
    model = TurnBackOrderItemForm
    template_name = 'item_form.html'


class InventoryOrderListView(FilterListView):
    model = InventoryOrder
    filter_class = InventoryOrderFilter


class InventoryOrderDetailView(StateChangeMixin, DetailView, MultipleObjectMixin):
    model = InventoryOrder

    def get_btn_visible(self, state):
        btn_visible = {}
        if state == 'draft':
            btn_visible.update({'confirm': True, 'cancel': True, 'delete': True})
        elif state == 'confirm':
            btn_visible.update({'done': True, 'draft': True})
        return btn_visible

    def confirm(self):
        return self.object.confirm()

    def done(self):
        return self.object.done()

    def draft(self):
        return self.object.draft()

    def get_context_data(self, **kwargs):
        items = self.object.items.all()
        filter = ProductFilter(self.request.GET, queryset=items)
        kwargs['filter'] = filter
        return super().get_context_data(object_list=filter.qs.distinct(), **kwargs)


class InventoryOrderDeleteView(ViewPermissionRequiredMixin, BaseDeleteView):
    model = InventoryOrder

    def get_success_url(self):
        return reverse_lazy('inventory_order_list')


class InventoryOrderEditMixin(OrderFormInitialEntryMixin):
    model = InventoryOrder
    template_name = 'form.html'
    form_class = InventoryOrderForm
    product_type = None

    def get_items(self):
        # 先按条件选出库存
        if self.object.items.all():
            return self.object.items.all()
        location_ids_list = self.object.warehouse.get_main_location().get_child_list()
        kwargs = {'location_id__in': location_ids_list}
        if self.object.product_type:
            kwargs['product__type'] = self.object.product_type
        start = time.clock()
        stocks = Stock.objects.prefetch_related('items').filter(**kwargs)
        # long running
        # do something other

        # print(Stock.objects.filter(**kwargs).distinct().explain())
        # 把需要盘点的所有先有库存创建items
        # i = 0
        for stock in stocks:
            old_item = {
                'order': self.object,
                'product': stock.product,
                'uom': stock.uom,
                'old_location': stock.location,
                # 'now_location': stock.location,
                'old_piece': stock.piece,
                'now_piece': stock.piece,
                'old_quantity': stock.quantity,
                'now_quantity': stock.quantity,
            }
            # 如果是板材，就用在库的slab新建一张码单,并把now_package_list 及package_list建为一张吉码单
            if stock.product.type == 'slab':
                slab_ids = stock.items.values_list('id', flat=True)
                package = PackageList.make_package_from_list(stock.product.id, slab_ids)
                # print('old_pg')
                old_item['old_package_list'] = package
                old_item['now_package_list'] = package.copy(has_items=True)
                # print('now_pg')
                # old_item['package_list'] = package.copy(has_items=True)
                old_item['package_list'] = package.copy(has_items=False)
                # print('pg')
                # print(i)
                # i += 1
            InventoryOrderItem.objects.create(**old_item)
        # InventoryOrderItem.objects.bulk_create(items_lst)
        end = time.clock()
        print(end - start)

    # @transaction.atomic()
    def form_valid(self, form):
        self.object = form.save()
        self.get_items()
        return super().form_valid(form)


class InventoryOrderCreateView(InventoryOrderEditMixin, CreateView):
    pass


class InventoryOrderUpdateView(InventoryOrderEditMixin, UpdateView):
    pass


class InventoryOrderItemSetCheckView(View):
    model = InventoryOrderItem

    def post(self, *args, **kwargs):
        pk = self.request.POST.get('pk')
        if pk:
            item = self.model.objects.get(pk=pk)
            if item.is_check:
                item.is_check = False
            else:
                item.is_check = True
            item.save()
            return JsonResponse({'state': 'ok', 'check': item.is_check})
        return JsonResponse({'state': 'error'})


class InventoryOrderItemEditView(OrderItemEditMixin):
    model = InventoryOrderItem
    form_class = InventoryOrderItemForm


class InventoryOrderNewItemEditView(OrderItemEditMixin):
    model = InventoryOrderNewItem
    form_class = InventoryOrderNewItemForm


class InventoryOrderNewItemDeleteView(OrderItemDeleteMixin):
    model = InventoryOrderNewItem


class MrpSupplierListView(FilterListView):
    from sales.filters import CustomerFilter
    model = MrpSupplier
    filter_class = CustomerFilter
    paginate_by = 10
    template_name = 'mrp/supplier_list.html'


class MrpSupplierDetailView(DynamicPermissionRequiredMixin, DetailView):
    model = MrpSupplier
    template_name = 'mrp/supplier_detail.html'


class SupplierEditMixin(DynamicPermissionRequiredMixin):
    model = MrpSupplier
    form_class = SupplierForm
    template_name = 'sales/form.html'

    def get_initial(self):
        initial = super().get_initial()
        initial['entry'] = self.request.user.id
        return initial


class SupplierCreateView(SupplierEditMixin, CreateView):
    pass


class SupplierUpdateView(SupplierEditMixin, UpdateView):
    pass


class MoveOrderToPdfView(BaseDetailView, PDFTemplateView):
    # show_content_in_browser = True
    model = MoveLocationOrder
    # header_template = 'sales/header.html'
    template_name = 'mrp/pdf/move_order_pdf.html'
    # footer_template = 'sales/footer.html'
    cmd_options = {
        'page-height': '19cm',
        'page-width': '13cm',
        'margin-top': '0',
        'margin-left': '0',
        'margin-bottom': '0',
        'margin-right': '0',
    }
