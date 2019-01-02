from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import ListView, DetailView
from django.views.generic.edit import ModelFormMixin, CreateView, UpdateView, BaseDeleteView
from django.contrib import messages

from invoice.models import CreateInvoice
from mrp.filters import InOutOrderFilter, MoveLocationOrderFilter, ProductionOrderFilter, InventoryOrderFilter
from mrp.models import ProductionOrder, ProductionOrderRawItem, ProductionOrderProduceItem, ProductionType, InOutOrder, \
    InOutOrderItem, Expenses, ExpensesItem, InventoryOrder, InventoryOrderItem, InventoryOrderNewItem
from mrp.models import TurnBackOrder, TurnBackOrderItem
from product.models import PackageList
from public.utils import Package, StockOperateItem
from public.views import OrderItemEditMixin, OrderItemDeleteMixin, OrderFormInitialEntryMixin, FilterListView
from public.widgets import SwitchesWidget
from purchase.models import PurchaseOrder
from public.views import GetItemsMixin, StateChangeMixin
from public.stock_operate import StockOperate
from sales.models import SalesOrder
from stock.models import Stock, Location
from .models import MoveLocationOrder, MoveLocationOrderItem
from .forms import MoveLocationOrderItemForm, MoveLocationOrderForm, ProductionOrderForm, \
    ProductionOrderRawItemForm, ProductionOrderProduceItemForm, InOutOrderForm, MrpItemExpensesForm, TurnBackOrderForm, \
    TurnBackOrderItemForm, InventoryOrderForm, InventoryOrderItemForm, InventoryOrderNewItemForm


class MoveLocationOrderListView(FilterListView):
    model = MoveLocationOrder
    filter_class = MoveLocationOrderFilter


class MoveLocationOrderDetailView(StateChangeMixin, GetItemsMixin, DetailView):
    model = MoveLocationOrder

    def get_btn_visible(self, state):
        btn_visible = {}
        if state == 'draft':
            btn_visible.update({'done': True, 'confirm': True, 'cancel': True})
        elif state == 'confirm':
            btn_visible.update({'done': True, 'draft': True})
        elif state == 'done':
            btn_visible.update({'turn_back': True})
        return btn_visible

    def done(self):
        return self.object.done()

    def confirm(self):
        return self.object.confirm()

    def draft(self):
        return self.object.draft()


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
        form.fileds['activate'].widget = SwitchesWidget()
        return form


class ProductionTypeUpdateView(UpdateView):
    model = ProductionType
    fields = '__all__'
    template_name = 'mrp/form.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fileds['activate'].widget = SwitchesWidget()
        return form


class ProductionOrderListView(FilterListView):
    model = ProductionOrder
    filter_class = ProductionOrderFilter


class ProductionOrderDetailView(StateChangeMixin, DetailView):
    model = ProductionOrder

    def get_btn_visible(self, state):
        btn_visible = {}
        if state == 'draft':
            btn_visible.update({'done': True, 'cancel': True})
        elif state == 'done':
            btn_visible.update({'turn_back': True})
        return btn_visible

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


class InOutOrderDetailView(StateChangeMixin, DetailView):
    model = InOutOrder

    def get_btn_visible(self, state):
        btn_visible = {}
        if state == 'draft':
            btn_visible.update({'done': True, 'delete': True})
        elif state == 'done':
            btn_visible.update({'turn_back': True})
        return btn_visible

    def done(self):
        return self.object.done()

    def cancel(self):
        return self.object.cancel()


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

    def get_purchase_order_items(self):
        # 如果是新建状态
        # 该采购单已收货的items取出
        already_check_in_items = self.purchase_order.items.filter(
            order__in_out_order__state__in=('confirm', 'done'))
        purchase_order_items = self.purchase_order.items.all()
        if already_check_in_items:
            purchase_order_items.exclude(product_id__in=[item.product.id for item in already_check_in_items])
        for item in purchase_order_items:
            InOutOrderItem.objects.create(product=item.product, piece=item.piece,
                                          quantity=item.quantity,
                                          uom=item.uom, order=self.object, purchase_order_item=item)
        return self.object.items.all()

    def get_sales_order_items(self):
        # 选出产品类型为荒料的已出货项的
        already_check_out_items = self.sales_order.items.filter(
            order__in_out_order__state__in=('confirm', 'done'), product__type='block')
        sales_order_items = self.sales_order.items.all()
        if already_check_out_items:
            sales_order_items.exclude(product_id__in=[item.product.id for item in already_check_out_items])
        if sales_order_items:
            # 生成新item的项目
            for item in sales_order_items:
                package = None
                if item.product.type == 'slab':
                    # slabs_id_lst = [item.get_slab_id() for item in
                    #                 item.package_list.items.filter(slab__stock__isnull=False,
                    #                                                slab__stock__location=self.object.warehouse.get_main_location())]
                    # 如果有码单，就生成一张新码单，并把码单的from_package_list链接到旧的码单，
                    # 为了在提货单draft状态下可以选择到旧码单的slab
                    # ps：后来更改为建一张空码单， 提货时候再选择
                    package = item.package_list.make_package_from_list(item.product_id,
                                                                       from_package_list=item.package_list)
                defaults = {'piece': item.piece if not package else package.get_piece(),
                            'quantity': item.quantity if not package else package.get_quantity(),
                            'package_list': package, 'product': item.product, 'order': self.object,
                            'uom': item.uom, 'sales_order_item': item}
                InOutOrderItem.objects.create(**defaults)
        return self.object.items.all()

    def get_items(self):
        # 如果是update状态，有object就返回items
        if self.object:
            items = self.object.items.all()
            if items:
                return items
        if self.purchase_order:
            return self.get_purchase_order_items()
        return self.get_sales_order_items()

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()
            self.get_items()
            return super().form_valid(form)


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
        if form.is_valid:
            self.object = form.save()
            return JsonResponse({'state': 'ok'})
        return HttpResponse(render_to_string(self.template_name, context))


class MrpExpensesItemListView(ListView):
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


class InventoryOrderDetailView(StateChangeMixin, DetailView):
    model = InventoryOrder

    def get_btn_visible(self, state):
        btn_visible = {}
        if state == 'draft':
            btn_visible.update({'done': True, 'confirm': True, 'cancel': True})
        elif state == 'confirm':
            btn_visible.update({'done': True, 'draft': True})
        return btn_visible

    def confirm(self):
        return self.object.confirm()

    def done(self):
        return self.object.done()

    def draft(self):
        return self.object.draft()


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
        stocks = Stock.objects.filter(**kwargs).distinct()
        # 把需要盘点的所有先有库存创建items
        for stock in stocks:
            old_item = {
                'order': self.object,
                'product': stock.product,
                'uom': stock.uom,
                'old_location': stock.location,
                'now_location': stock.location,
                'old_piece': stock.piece,
                'now_piece': stock.piece,
                'old_quantity': stock.quantity,
                'now_quantity': stock.quantity,
            }
            # 如果是板材，就新建一张吉码单
            if stock.product.type == 'slab':
                slab_ids = stock.items.all().values_list('id', flat=True)
                package = PackageList.make_package_from_list(stock.product.id, slab_ids)
                old_item['old_package_list'] = package
                old_item['now_package_list'] = package.copy()
                old_item['package_list'] = package.copy()
            InventoryOrderItem.objects.create(**old_item)

    @transaction.atomic()
    def form_valid(self, form):
        self.object = form.save()
        self.get_items()
        return super().form_valid(form)


class InventoryOrderCreateView(InventoryOrderEditMixin, CreateView):
    pass


class InventoryOrderUpdateView(InventoryOrderEditMixin, UpdateView):
    pass


class InventoryOrderItemEditView(OrderItemEditMixin):
    model = InventoryOrderItem
    form_class = InventoryOrderItemForm


class InventoryOrderNewItemEditView(OrderItemEditMixin):
    model = InventoryOrderNewItem
    form_class = InventoryOrderNewItemForm


class InventoryOrderNewItemDeleteView(OrderItemDeleteMixin):
    model = InventoryOrderNewItem
