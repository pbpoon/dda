from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.views.generic.edit import ModelFormMixin, CreateView, UpdateView
from django.contrib import messages

from purchase.models import PurchaseOrder
from purchase.views import GetItemsMixin, StateChangeMixin
from stock.stock_operate import StockOperate
from .models import BlockCheckInOrder, BlockCheckInOrderItem
from .forms import BlockCheckOrderForm


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
        stock = StockOperate(self.request, items=self.object.items.all(), order=self.object,
                             location=self.object.location,
                             location_dest=self.object.location_dest)
        stock, message = stock.handle_stock()
        if stock:
            messages.success(self.request, message)
            self.object.state = 'done'
            self.object.save()
        else:
            messages.error(self.request, message)
        return super(BlockCheckInOrderDetailView, self).confirm()


class BlockCheckInOrderEditMixin:
    model = BlockCheckInOrder
    purchase_order = None
    form_class = BlockCheckOrderForm
    template_name = 'mrp/blockcheckinorder_form.html'

    def get_context_data(self, **kwargs):
        items = self.get_items()
        kwargs.update({'object_list': items})
        return super(BlockCheckInOrderEditMixin, self).get_context_data(**kwargs)

    def get_initial(self):
        kwargs = super(BlockCheckInOrderEditMixin, self).get_initial()
        kwargs.update({'entry': self.request.user,
                       'purchase_order': self.purchase_order})
        return kwargs

    def get_items(self):
        # 如果是udate状态，有object就返回items
        if self.object:
            return self.object.items.all()
        # 如果是新建状态
        # 该采购单已收货的items取出
        already_check_in_items = self.purchase_order.items.filter(
            order__block_check_in_order__state__in=('confirm', 'done'))
        purchase_order_items = self.purchase_order.items.all()
        if already_check_in_items:
            purchase_order_items.filter(product_id__exact=[item.product.id for item in already_check_in_items])
        for item in purchase_order_items:
            item, _ = BlockCheckInOrderItem.objects.get_or_create(product=item.product, piece=1,
                                                                  quantity=item.product.weight if item.product.uom == 't' else item.product.get_m3(),
                                                                  uom=item.uom)
        items = BlockCheckInOrderItem.objects.filter(product_id__in=[item.product.id for item in purchase_order_items],
                                                     order__isnull=True)
        return items

    def dispatch(self, request, purchase_order_id):
        self.purchase_order = get_object_or_404(PurchaseOrder, pk=purchase_order_id, state__in=('confirm', 'done'))
        return super(BlockCheckInOrderEditMixin, self).dispatch(request, purchase_order_id)

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.location = self.purchase_order.partner.get_location()
        obj.location_dest = obj.warehouse.get_main_location()
        obj.save()
        items = self.get_items()
        items.update(order=obj)
        return super(BlockCheckInOrderEditMixin, self).form_valid(form)


class BlockCheckInOrderCreateView(BlockCheckInOrderEditMixin, CreateView):
    pass


class BlockCheckInOrderUpdateView(StateChangeMixin, BlockCheckInOrderEditMixin, UpdateView):
    pass


