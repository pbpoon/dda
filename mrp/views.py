from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import ListView, DetailView
from django.views.generic.edit import ModelFormMixin, CreateView, UpdateView, BaseDeleteView
from django.contrib import messages

from invoice.models import CreateInvoice
from mrp.models import ProductionOrder, ProductionOrderRawItem, ProductionOrderProduceItem, ProductionType, InOutOrder, \
    InOutOrderItem, Expenses, ExpensesItem, InventoryOrder, InventoryOrderItem
from mrp.models import TurnBackOrder, TurnBackOrderItem
from product.models import PackageList
from public.utils import Package
from public.views import OrderItemEditMixin, OrderItemDeleteMixin, OrderFormInitialEntryMixin
from purchase.models import PurchaseOrder
from public.views import GetItemsMixin, StateChangeMixin
from public.stock_operate import StockOperate
from sales.models import SalesOrder
from stock.models import Stock
from .models import MoveLocationOrder, MoveLocationOrderItem
from .forms import MoveLocationOrderItemForm, MoveLocationOrderForm, ProductionOrderForm, \
    ProductionOrderRawItemForm, ProductionOrderProduceItemForm, InOutOrderForm, MrpItemExpensesForm, TurnBackOrderForm, \
    TurnBackOrderItemForm, InventoryOrderForm, InventoryOrderItemForm


class MoveLocationOrderListView(ListView):
    model = MoveLocationOrder


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
        stock = StockOperate(self.request, order=self.object, items=self.object.items.all())
        if self.object.state == 'confirm':
            stock.reserve_stock(unlock=True)
        return stock.handle_stock()

    def confirm(self):
        stock = StockOperate(self.request, order=self.object, items=self.object.items.all())
        return stock.reserve_stock()

    def draft(self):
        stock = StockOperate(self.request, order=self.object, items=self.object.items.all())
        return stock.reserve_stock(unlock=True)


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


class ProductionTypeUpdateView(UpdateView):
    model = ProductionType
    fields = '__all__'
    template_name = 'mrp/form.html'


class ProductionOrderListView(ListView):
    model = ProductionOrder


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
        items = [i for i in self.object.items.all()]
        items.extend([i for i in self.object.produce_items.all()])
        stock = StockOperate(self.request, order=self.object, items=items)
        return stock.handle_stock()


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


class InOutOrderListView(ListView):
    model = InOutOrder


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
        stock = StockOperate(self.request, self.object, self.object.items.all())
        unlock, msg = stock.reserve_stock(unlock=True)
        if unlock:
            return stock.handle_stock()
        return unlock, msg


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
                                          uom=item.uom, order=self.object)
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
                    slabs_id_lst = [item.get_slab_id() for item in
                                    item.package_list.items.filter(slab__stock__isnull=False,
                                                                   slab__stock__location=self.object.warehouse.get_main_location())]
                    # 如果有码单，就生成一张新码单，并把码单的from_package_list链接到旧的码单，
                    # 为了在提货单draft状态下可以选择到旧码单的slab
                    package = item.package_list.make_package_from_list(item.product_id, slabs_id_lst,
                                                                       from_package_list=item.package_list)
                defaults = {'piece': item.piece if not package else package.get_piece(),
                            'quantity': item.quantity if not package else package.get_quantity(),
                            'package_list': package, 'product': item.product, 'order': self.object,
                            'uom': item.uom}
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
            return self.form_valid(form)
        return HttpResponse(render_to_string(self.template_name, context))

    def form_valid(self, form):
        self.object = form.save()
        return JsonResponse({'state': 'ok'})


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
        items = self.object.items.all()
        stock = StockOperate(self.request, order=self.object, items=items)
        form_order = self.object.get_obj()
        form_order.state = 'cancel'
        # form_order.comments.create(user=self.request.user, content='由%s设置状态：取消，原因是：%s' % (self.object, self.object.reason),)
        form_order.save()
        return stock.handle_stock()


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
                items = [item for item in items]
                items.extend([item for item in self.from_order.produce_items.all()])
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


class InventoryOrderListView(ListView):
    model = InventoryOrder


class InventoryOrderDetailView(DetailView):
    model = InventoryOrder


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
                'location': stock.location,
                'old_piece': stock.piece,
                'old_quantity': stock.quantity,
            }
            # 如果是板材，就把建一张码单
            if stock.product.type == 'slab':
                slab_ids = stock.items.all().values_list('id')
                old_item['old_package_list'] = PackageList.make_package_from_list(stock.product.id, slab_ids)
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