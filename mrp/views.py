from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect, render_to_response
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import ListView, DetailView, TemplateView
from django.views.generic.edit import ModelFormMixin, CreateView, UpdateView, DeleteView, BaseDeleteView
from django.contrib import messages

from invoice.models import CreateInvoice
from mrp.models import ProductionOrder, ProductionOrderRawItem, ProductionOrderProduceItem, ProductionType, InOutOrder, \
    InOutOrderItem, Expenses, ExpensesItem
from public.views import OrderItemEditMixin, OrderItemDeleteMixin, OrderFormInitialEntryMixin
from purchase.models import PurchaseOrder
from public.views import GetItemsMixin, StateChangeMixin
from public.stock_operate import StockOperate
from sales.models import SalesOrder
from .models import MoveLocationOrder, MoveLocationOrderItem
from .forms import MoveLocationOrderItemForm, MoveLocationOrderForm, ProductionOrderForm, \
    ProductionOrderRawItemForm, ProductionOrderProduceItemForm, InOutOrderForm, MrpItemExpensesForm


#
# class BlockCheckInOrderListView(ListView):
#     model = BlockCheckInOrder
#
#
# class BlockCheckInOrderDetailView(StateChangeMixin, GetItemsMixin, DetailView):
#     model = BlockCheckInOrder
#
#     def get_btn_visible(self, state):
#         btn_visible = {}
#         if state == 'draft':
#             btn_visible.update({'done': True, 'cancel': True})
#         elif state == 'done':
#             btn_visible.update({'draft': False, 'cancel': False})
#         return btn_visible
#
#     def done(self):
#         stock = StockOperate(self.request, items=self.object.items.all(), order=self.object)
#         return stock.handle_stock()
#
#
# class BlockCheckInOrderEditMixin:
#     model = BlockCheckInOrder
#     purchase_order = None
#     form_class = BlockCheckInOrderForm
#     template_name = 'mrp/blockcheckinorder_form.html'
#
#     def get_initial(self):
#         kwargs = super(BlockCheckInOrderEditMixin, self).get_initial()
#         kwargs.update({'entry': self.request.user,
#                        'purchase_order': self.purchase_order})
#         return kwargs
#
#     def get_items(self):
#         # 如果是update状态，有object就返回items
#         if self.object:
#             items = self.object.items.all()
#             if items:
#                 return items
#         # 如果是新建状态
#         # 该采购单已收货的items取出
#         already_check_in_items = self.purchase_order.items.filter(
#             order__block_check_in_order__state__in=('confirm', 'done'))
#         purchase_order_items = self.purchase_order.items.all()
#         if already_check_in_items:
#             purchase_order_items.exclude(product_id__in=[item.product.id for item in already_check_in_items])
#         for item in purchase_order_items:
#             item, _ = BlockCheckInOrderItem.objects.get_or_create(product=item.product, piece=item.piece,
#                                                                   quantity=item.quantity,
#                                                                   uom=item.uom, order=self.object)
#         # items = BlockCheckInOrderItem.objects.filter(product_id__in=[item.product.id for item in purchase_order_items],
#         #                                              order__isnull=True)
#         return self.object.items.all()
#
#     def dispatch(self, request, purchase_order_id):
#         self.purchase_order = get_object_or_404(PurchaseOrder, pk=purchase_order_id, state__in=('confirm', 'done'))
#         if not self.purchase_order:
#             raise ValueError('创建提货单错误')
#         return super(BlockCheckInOrderEditMixin, self).dispatch(request, purchase_order_id)
#
#     def form_valid(self, form):
#         self.object = form.save()
#         items = self.get_items()
#         return super(BlockCheckInOrderEditMixin, self).form_valid(form)
#
#
# class BlockCheckInOrderCreateView(BlockCheckInOrderEditMixin, CreateView):
#     pass
#
#
# class BlockCheckInOrderUpdateView(StateChangeMixin, BlockCheckInOrderEditMixin, UpdateView):
#     pass
#
#
# class BlockCheckInOrderItemEditView(OrderItemEditMixin):
#     model = BlockCheckInOrderItem
#     form_class = BlockCheckInOrderItemForm
#
#     def get_order(self):
#         order = None
#         order_id = self.get_order_id()
#         if self.object:
#             order = self.object.order
#         elif order_id:
#             order = MoveLocationOrder.objects.get(pk=order_id)
#         return order
#
#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs['block_check_in_order'] = self.get_order()
#         return kwargs
#
#
# class BlockCheckInOrderItemDeleteView(OrderItemDeleteMixin):
#     model = BlockCheckInOrderItem


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
            btn_visible.update({'done': True, 'cancel': True})
        elif state == 'done':
            btn_visible.update({'draft': False, 'cancel': False})
        return btn_visible

    def done(self):
        stock = StockOperate(self.request, self.object, self.object.items.all())
        unlock, msg = stock.reserve_stock(unlock=True)
        if unlock:
            return stock.handle_stock()
        return unlock, msg

    def cancel(self):
        from_order = self.object.sales_order or self.object.purchase_order
        success_url = from_order.get_absolute_url()
        self.object.delete()
        return redirect(success_url)


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
            self.purchase_order = get_object_or_404(SalesOrder, pk=kwargs.get('purchase_order_id'))
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
                slabs_id_lst = [item.get_slab_id() for item in item.package_list.items.filter(slab__stock__isnull=False,
                                                                                              slab__stock__location=self.object.warehouse.get_main_location())]
                package = None
                # 如果有码单，就生成一张新码单，并把码单的from_package_list链接到旧的码单，
                # 为了在提货单draft状态下可以选择到旧码单的slab
                if slabs_id_lst:
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
