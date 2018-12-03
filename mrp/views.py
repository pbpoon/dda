from django.shortcuts import render, get_object_or_404, redirect, render_to_response
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, TemplateView
from django.views.generic.edit import ModelFormMixin, CreateView, UpdateView, DeleteView, BaseDeleteView
from django.contrib import messages
from django import forms

from invoice.models import CreateInvoice
from mrp.models import ProductionOrder, ProductionOrderRawItem, ProductionOrderProduceItem, ProductionType
from product.models import Product
from public.views import OrderItemEditMixin, OrderItemDeleteMixin, OrderFormInitialEntryMixin
from purchase.models import PurchaseOrder
from public.views import GetItemsMixin, StateChangeMixin
from public.stock_operate import StockOperate
from .models import BlockCheckInOrder, BlockCheckInOrderItem, KesOrder, KesOrderRawItem, KesOrderProduceItem, \
    MoveLocationOrder, MoveLocationOrderItem
from .forms import BlockCheckInOrderForm, KesOrderRawItemForm, KesOrderProduceItemForm, KesOrderForm, \
    BlockCheckInOrderItemForm, MoveLocationOrderItemForm, MoveLocationOrderForm, ProductionOrderForm, \
    ProductionOrderRawItemForm, ProductionOrderProduceItemForm


class BlockCheckInOrderListView(ListView):
    model = BlockCheckInOrder


class BlockCheckInOrderDetailView(StateChangeMixin, GetItemsMixin, DetailView):
    model = BlockCheckInOrder

    def get_btn_visible(self, state):
        btn_visible = {}
        if state == 'draft':
            btn_visible.update({'done': True, 'cancel': True})
        elif state == 'done':
            btn_visible.update({'draft': False, 'cancel': False})
        return btn_visible

    def done(self):
        stock = StockOperate(self.request, items=self.object.items.all(), order=self.object)
        return stock.handle_stock()


class BlockCheckInOrderEditMixin:
    model = BlockCheckInOrder
    purchase_order = None
    form_class = BlockCheckInOrderForm
    template_name = 'mrp/blockcheckinorder_form.html'

    def get_initial(self):
        kwargs = super(BlockCheckInOrderEditMixin, self).get_initial()
        kwargs.update({'entry': self.request.user,
                       'purchase_order': self.purchase_order})
        return kwargs

    def get_items(self):
        # 如果是update状态，有object就返回items
        if self.object:
            items = self.object.items.all()
            if items:
                return items
        # 如果是新建状态
        # 该采购单已收货的items取出
        already_check_in_items = self.purchase_order.items.filter(
            order__block_check_in_order__state__in=('confirm', 'done'))
        purchase_order_items = self.purchase_order.items.all()
        if already_check_in_items:
            purchase_order_items.exclude(product_id__in=[item.product.id for item in already_check_in_items])
        for item in purchase_order_items:
            item, _ = BlockCheckInOrderItem.objects.get_or_create(product=item.product, piece=item.piece, quantity=item.quantity,
                                                                  uom=item.uom, order=self.object)
        # items = BlockCheckInOrderItem.objects.filter(product_id__in=[item.product.id for item in purchase_order_items],
        #                                              order__isnull=True)
        return self.object.items.all()

    def dispatch(self, request, purchase_order_id):
        self.purchase_order = get_object_or_404(PurchaseOrder, pk=purchase_order_id, state__in=('confirm', 'done'))
        if not self.purchase_order:
            raise ValueError('创建提货单错误')
        return super(BlockCheckInOrderEditMixin, self).dispatch(request, purchase_order_id)

    def form_valid(self, form):
        self.object = form.save()
        items = self.get_items()
        return super(BlockCheckInOrderEditMixin, self).form_valid(form)


class BlockCheckInOrderCreateView(BlockCheckInOrderEditMixin, CreateView):
    pass


class BlockCheckInOrderUpdateView(StateChangeMixin, BlockCheckInOrderEditMixin, UpdateView):
    pass


class BlockCheckInOrderItemEditView(OrderItemEditMixin):
    model = BlockCheckInOrderItem
    form_class = BlockCheckInOrderItemForm

    def get_order(self):
        order = None
        order_id = self.get_order_id()
        if self.object:
            order = self.object.order
        elif order_id:
            order = MoveLocationOrder.objects.get(pk=order_id)
        return order

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['block_check_in_order'] = self.get_order()
        return kwargs


class BlockCheckInOrderItemDeleteView(OrderItemDeleteMixin):
    model = BlockCheckInOrderItem


# ------------------------------ Kes Order ----------------------------------

class KesOrderListView(ListView):
    model = KesOrder


class KesOrderDetailView(StateChangeMixin, GetItemsMixin, DetailView):
    model = KesOrder

    def confirm(self):
        items = [i for i in self.object.items.all()]
        items.extend([i for i in self.object.produce_items.all()])
        stock = StockOperate(self.request, order=self.object, items=items)
        return stock.handle_stock()

    def make_invoice(self):
        items = [{'item': str(item.product), 'quantity': item.quantity, 'price': item.price} for item in
                 self.object.items.all()]
        # CreateInvoice(self.object, self.object.partner, self.request.user, items)
        # 写好其他再回来写
        return True


class KesOrderEditMixin(OrderFormInitialEntryMixin):
    model = KesOrder
    form_class = KesOrderForm
    template_name = 'mrp/form.html'


class KesOrderUpdateView(KesOrderEditMixin, UpdateView):
    pass


class KesOrderCreateView(KesOrderEditMixin, CreateView):
    pass


class KesOrderRawItemEditView(OrderItemEditMixin):
    """
    原材料（荒料）创建与编辑
    """
    form_class = KesOrderRawItemForm
    model = KesOrderRawItem

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        order_id = self.request.GET.get('order_id', None)
        order = None
        if order_id:
            order = KesOrder.objects.get(pk=order_id)
        kwargs.update({'kes_order': order})
        return kwargs


class KesOrderRawItemDeleteView(BaseDeleteView):
    """
        原材料（荒料）删除
    """
    model = KesOrderRawItem

    def get_success_url(self):
        return self.request.META.get('HTTP_REFERER')


class KesOrderProduceItemEditView(OrderItemEditMixin):
    """
        成品（毛板）创建与编辑
    """
    model = KesOrderProduceItem
    form_class = KesOrderProduceItemForm

    def get_initial(self):
        initial = super(KesOrderProduceItemEditView, self).get_initial()
        raw_item_id = self.request.GET.get('raw_item_id', None)
        if raw_item_id:
            initial['raw_item'] = raw_item_id
        return initial


class KesOrderProduceItemDeleteView(OrderItemDeleteMixin):
    """
       成品（毛板）删除
    """
    model = KesOrderProduceItem


# -----------------------------------move location--------------
class MoveLocationOrderListView(ListView):
    model = MoveLocationOrder


class MoveLocationOrderDetailView(StateChangeMixin, GetItemsMixin, DetailView):
    model = MoveLocationOrder

    def get_btn_visible(self, state):
        btn_visible = {}
        if state == 'draft':
            btn_visible.update({'done': True, 'cancel': True})
        elif state == 'done':
            btn_visible.update({'draft': False, 'cancel': False})
        return btn_visible

    def done(self):
        items = self.object.items.all()
        stock = StockOperate(self.request, order=self.object, items=items)
        return stock.handle_stock()


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

    def get_order(self):
        order = None
        order_id = self.get_order_id()
        if self.object:
            order = self.object.order
        elif order_id:
            order = MoveLocationOrder.objects.get(pk=order_id)
        return order

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['move_order'] = self.get_order()
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

    def confirm(self):
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

    def get_order(self):
        order = None
        order_id = self.get_order_id()
        if self.object:
            order = self.object.order
        elif order_id:
            order = ProductionOrder.objects.get(pk=order_id)
        return order

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['production_order'] = self.get_order()
        return kwargs


class ProductionOrderRawItemEditView(ProductionOrderItemEditMixin):
    model = ProductionOrderRawItem
    form_class = ProductionOrderRawItemForm

    def get_initial(self):
        initial = super().get_initial()
        initial['location'] = self.get_order().location.id
        return initial


class ProductionOrderRawItemDeleteView(OrderItemDeleteMixin):
    model = ProductionOrderRawItem


class ProductionOrderProduceItemEditView(ProductionOrderItemEditMixin):
    model = ProductionOrderProduceItem
    form_class = ProductionOrderProduceItemForm

    def get_initial(self):
        initial = super().get_initial()
        raw_item_id = self.request.GET.get('raw_item_id', None)
        if raw_item_id:
            initial['raw_item'] = raw_item_id
        return initial


class ProductionOrderProduceItemDeleteView(OrderItemDeleteMixin):
    model = ProductionOrderProduceItem
