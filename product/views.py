from django.apps import apps
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, HttpResponse, redirect
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from cart.cart import Cart
from product.filters import BlockFilter
from product.forms import DraftPackageListItemForm, PackageListItemForm, PackageListItemEditForm, \
    PackageListItemMoveForm
from public.views import OrderItemEditMixin, OrderItemDeleteMixin, ModalOptionsMixin, FilterListView
from stock.models import Location, Stock, Warehouse
from public.utils import qs_to_dict, Package

from .models import Product, PackageList, DraftPackageList, DraftPackageListItem, Slab, Block, PackageListItem, \
    Category, Quarry


def get_block_list(request):
    name = request.POST.get('name_autocomplete')
    qs = Block.objects.filter(name__icontains=name)
    data = {str(p): {"id": p.id, 'image': None} for p in qs}
    return JsonResponse(data, safe=False)


def get_product_info(request):
    product_id = request.GET.get('product')
    location_id = request.GET.get('location')
    product = get_object_or_404(Product, pk=product_id)
    location = get_object_or_404(Location, pk=location_id) if location_id else None
    piece, quantity = product.get_available(location=location)
    data = {'piece': piece, 'quantity': quantity}
    return JsonResponse(data)


def get_product_list(request):
    loc_id = request.POST.get('location')  # production form 传来
    wh_id = request.POST.get('warehouse')  # sale_order form 传来
    type = request.POST.get('type', None)  # production form 传来
    qs = Product.objects.all()
    product_text = request.POST.get('product_autocomplete')
    if product_text:
        qs = qs.filter(block__name__icontains=product_text)
    if wh_id:
        loc_childs = Warehouse.objects.get(pk=wh_id).get_main_location().get_child_list()
        qs = qs.filter(stock__location_id__in=loc_childs)
    elif loc_id:
        loc_childs = Location.objects.get(pk=loc_id).get_main_location().get_child_list()
        qs = qs.filter(stock__location_id__in=loc_childs)
        # loc_childs = Location.objects.get(pk=loc_id).get_child_list()
    if type:
        qs = qs.filter(type=type)
    else:
        qs = qs.exclude(type='semi_slab')
    qs.distinct()
    data = {str(p): {"id": p.id} for p in qs}
    return JsonResponse(data, safe=False)


def get_draft_package_list_info(request):
    pk = request.GET.get('pk')
    obj = get_object_or_404(DraftPackageList, pk=pk)
    if obj:
        data = {'state': 'ok',
                'draft_package_list': obj.id,
                'piece': obj.get_total_piece(),
                'quantity': str(obj.get_total_quantity())}
    else:
        data = {'status': 'error'}
    return JsonResponse(data)


class CategoryListView(ListView):
    model = Category


class CategoryEditMixin:
    model = Category
    fields = '__all__'
    template_name = 'form.html'


class CategoryCreateView(CategoryEditMixin, CreateView):
    pass


class CategoryUpdateView(CategoryEditMixin, UpdateView):
    pass


class CategoryDetailView(DetailView):
    model = Category


class QuarryListView(ListView):
    model = Quarry


class QuarryDetailView(DetailView):
    model = Quarry


class QuarryEditMixin:
    model = Quarry
    fields = '__all__'
    template_name = 'form.html'


class QuarryCreateView(QuarryEditMixin, CreateView):
    pass


class QuarryUpdateView(QuarryEditMixin, UpdateView):
    pass


class BlockListView(FilterListView):
    model = Block
    filter_class = BlockFilter


class BlockDetailView(DetailView):
    model = Block


class ProductListView(ListView):
    model = Product


class ProductDetailView(DetailView):
    model = Product


class DraftPackageListView(ListView):
    model = DraftPackageList
    template_name = 'choice_package_list.html'


class DraftPackageListDetailView(DetailView):
    model = DraftPackageList

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['part_number_list'] = set(item.part_number for item in self.object.items.all())
        context['package_list'] = self.make_package_list_display(self.object.items.all())
        return context

    def make_package_list_display(self, items):
        kw = {}
        for k in {item.part_number for item in items}:
            for item in items:
                if item.part_number == k:
                    kw.setdefault(k, []).append(item)
        return kw

    def post(self, *args, **kwargs):
        path = self.request.META.get('HTTP_REFERER')
        select_list = self.request.POST.getlist('select')
        if select_list:
            DraftPackageListItem.objects.filter(id__in=select_list).delete()
        return redirect(path)


class DraftPackageListQuickCreateView(View):
    model = DraftPackageList

    def post(self, *args, **kwargs):
        defaults = {}
        name = self.request.POST.get('raw_product_name')
        thickness = self.request.POST.get('raw_product_thickness')
        defaults['from_path'] = self.request.META.get('HTTP_REFERER')
        entry = self.request.user
        self.object, _ = self.model.objects.get_or_create(name=name, thickness=thickness, entry=entry,
                                                          defaults=defaults)
        return JsonResponse({'state': 'ok', 'url': self.object.get_absolute_url()})


class DraftPackageListCreateView(CreateView):
    model = DraftPackageList
    template_name = "form.html"
    fields = ('name', 'thickness', 'entry')

    def get_initial(self):
        initial = super().get_initial()
        initial['entry'] = self.request.user.id
        return initial


class DraftPackageListItemEditView(OrderItemEditMixin):
    model = DraftPackageListItem
    form_class = DraftPackageListItemForm


class DraftPackageListItemDeleteView(OrderItemDeleteMixin):
    model = DraftPackageListItem


# 一般order订单的码单显示
class PackageListDetail(DetailView):
    model = PackageList
    template_name = 'product/package_list.html'

    def get_state_draft_slabs(self):
        slabs = {item for stock in self.object.product.stock.all() for item in
                 stock.items.filter(is_reserve=False)}
        return slabs

    # 取出已经锁货的列表
    def get_is_reserve_list(self, slabs):
        if slabs:
            return [s.get_slab_id() for s in slabs if s.is_reserve]

    def get_context_data(self, **kwargs):
        state = self.request.GET.get('state')
        self.object = self.get_object()

        slabs = [item.slab for item in self.object.items.all()]
        package_slabs_ids = [s.get_slab_id() for s in slabs]

        if state == 'draft':
            slabs = self.get_state_draft_slabs()
        package = Package(self.object.product, slabs)

        is_reserve_list = self.get_is_reserve_list(slabs)
        cart = Cart(self.request)

        data = {'package': package, 'cart': cart, 'package_slabs_ids': package_slabs_ids,
                'state': state, 'object': self.object, 'is_reserve_list': is_reserve_list}
        return data

    def get(self, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return HttpResponse(render_to_string(self.template_name, context))

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        slab_list = self.request.POST.getlist('select')
        if slab_list:
            self.object.update(self.object, slab_list)
            data = {'state': 'ok'}
        else:
            message = '选择无效'
            data = {'state': 'error', 'message': message}
        return JsonResponse(data)


# 生产（板材入库）的码单draft显示
class ProductionOrderPackageListDetailView(PackageListDetail):

    def get_state_draft_slabs(self):
        slabs = [item.slab for item in self.object.items.all()]
        return slabs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        state = self.request.GET.get('state')
        context['add_new'] = True if state == 'draft' else False
        return context


# 库存盘点码单（编辑）显示
class InventoryOrderPackageListDetailView(PackageListDetail):
    template_name = 'product/inventory_package_list.html'

    def get(self, *args, **kwargs):
        state = self.request.GET.get('state')
        self.object = self.get_object()
        # 先把旧（库存）的码单slab取出
        old_slabs_ids = [s.get_slab_id() for s in self.object.from_package_list.items.all()]
        now_slabs_ids = [item.get_slab_id() for item in self.object.items.all()]

        slabs = Slab.objects.filter(id__in=set(now_slabs_ids) | set(old_slabs_ids))
        package = Package(self.object.product, slabs)

        data = {'object': self.object, 'package': package, 'old_slabs_ids': old_slabs_ids,
                'now_slabs_ids': now_slabs_ids,
                'state': state}
        return HttpResponse(render_to_string(self.template_name, data))


# 库存盘点码单（新建）显示
class InventoryOrderNewItemPackageListDetailView(PackageListDetail):
    template_name = 'product/inventory_package_list.html'

    def get(self, *args, **kwargs):
        state = self.request.GET.get('state')
        add_new = True if state == 'draft' else False
        self.object = self.get_object()
        now_slabs_ids = None
        package = None
        # 先把旧（库存）的码单slab取出
        if self.object.items.all():
            slabs_ids = [item.get_slab_id() for item in self.object.items.all()]
            slabs = Slab.objects.filter(id__in=slabs_ids)
            package = Package(self.object.product, slabs)
            now_slabs_ids = slabs_ids

        data = {'object': self.object, 'package': package, 'state': state, 'now_slabs_ids': now_slabs_ids,
                'add_new': add_new}
        return HttpResponse(render_to_string(self.template_name, data))


# 提货单的码单显示
class OutOrderPackageListDetailView(PackageListDetail):

    def get_is_reserve_list(self, slabs):
        return []

    def get_state_draft_slabs(self):
        slabs = list(self.object.from_package_list.items.filter(slab__stock__isnull=False))
        return slabs


# 销售订单项目码单创建
class OrderItemPackageListCreateView(View):
    template_name = 'product/package_list.html'

    def get(self, *args, **kwargs):
        location_id = self.kwargs.get('location_id')
        loc_ids = Location.objects.get(pk=location_id).get_child_list()
        product_id = self.kwargs.get('product_id')
        stock = Stock.objects.filter(product_id=product_id, product__type='slab', location_id__in=loc_ids).distinct()
        slabs = [slab for s in stock for slab in s.items.filter(is_reserve=False)]
        package = Package(Product.objects.get(pk=product_id), slabs)
        package_slabs_ids = None
        data = {'package': package, 'package_slabs_ids': package_slabs_ids, 'state': 'draft'}
        return HttpResponse(render_to_string(self.template_name, data))

    def post(self, *args, **kwargs):
        slab_list = self.request.POST.getlist('select')
        product_id = self.kwargs.get('product_id')
        app_label_lower = self.kwargs.get('app_label_lower')
        app_label, model_name = app_label_lower.split('.')
        package = PackageList.make_package_from_list(product_id, slab_list)
        item = apps.get_model(app_label=app_label, model_name=model_name).objects.get(pk=self.kwargs.get('item_id'))
        item.package_list = package
        item.piece = package.get_piece()
        item.quantity = package.get_quantity()
        item.save()
        return JsonResponse({'state': 'ok'})


# 销售单编辑状态，按location筛选
class SaleOrderPackageListView(PackageListDetail):
    location_id = None

    def get_state_draft_slabs(self):
        loc_ids = Location.objects.get(pk=self.location_id).get_child_list()
        slabs = {item for stock in self.object.product.stock.filter(location_id__in=loc_ids).distinct() for item in
                 stock.items.filter(is_reserve=False)}
        return slabs

    def dispatch(self, request, *args, **kwargs):
        self.location_id = kwargs.get('location_id')
        return super().dispatch(request, *args, **kwargs)


# 提货单的码单显示
class TurnBackOrderPackageListDetailView(PackageListDetail):

    def get_state_draft_slabs(self):
        slabs = [item.slab for item in self.object.from_package_list.items.all()]
        return slabs


class PackageListFullPageView(DetailView):
    model = PackageList
    template_name = 'product/packagelist_full_page.html'

    def get_context_data(self, **kwargs):
        self.object = self.get_object()
        state = self.request.GET.get('state')
        add_new = self.request.GET.get('add_new', False)
        if not self.object.return_path:
            return_path = self.request.META.get('HTTP_REFERER')
            self.model.objects.filter(pk=self.object.pk).update(return_path=return_path)
            self.object = self.get_object()
        slabs = [item.slab for item in self.object.items.all()]
        package_slabs_ids = [s.get_slab_id() for s in slabs]
        package = Package(self.object.product, slabs)
        cart = Cart(self.request)
        data = {'package': package, 'cart': cart, 'packsage_slabs_ids': package_slabs_ids,
                'object': self.object, 'state': state, 'add_new': add_new}
        kwargs.update(data)
        return super().get_context_data(**kwargs)


# 码单item添加
class PackageListItemCreateView(OrderItemEditMixin):
    model = PackageListItem
    form_class = PackageListItemForm


class PackageListItemEditView(OrderItemEditMixin):
    model = PackageListItem
    form_class = PackageListItemEditForm


class PackageListItemMoveView(ModalOptionsMixin):
    model = PackageList
    form_class = PackageListItemMoveForm

    def get_success_url(self):
        path = self.request.META.get('HTTP_REFERER')
        return path

    def get_options(self):
        select_slab_ids = self.request.GET.getlist('select')
        if select_slab_ids:
            return ((i, '第 %s 夹' % (i)) for i in range(1, 11))
        return (('nothing', '没有选择到需要移动到其他夹#的板材'),)

    def do_option(self, option):
        items_ids = self.request.POST.get('select_slab_ids')
        if items_ids:
            ids = items_ids.split(',')
            PackageListItem.objects.filter(id__in=ids).update(part_number=option)
        return True, ''

    def get_form(self):
        select_slab_ids = self.request.GET.getlist('select')
        items_ids = self.object.items.filter(slab_id__in=select_slab_ids).values_list(
            'id', flat=True)
        form = super().get_form()
        form.fields['select_slab_ids'].initial = ','.join([str(id) for id in items_ids])
        return form

    def get_content(self):
        select_slab_ids = self.request.GET.getlist('select')
        if not select_slab_ids:
            return '没有选择到需要移动到其他夹#的板材'
        return '请选择需要移动到那个夹#'


class PackageListItemLineUpdateView(DetailView):
    model = PackageList

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        part_number = {}
        for item in self.object.items.all().order_by('part_number', 'line'):
            part_number.setdefault(item.part_number, []).append(item)
        for k, v in part_number.items():
            _v = sorted(v, key=lambda x: x.line)
            for i, item in enumerate(_v, start=1):
                item.line = i
                item.save()
        path = self.request.META.get('HTTP_REFERER')
        return redirect(path)
