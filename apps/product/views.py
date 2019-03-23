import itertools
from collections import namedtuple

import xlrd
from django.apps import apps
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django import forms
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, HttpResponse, redirect
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.views.generic.detail import BaseDetailView
from django.views.generic.list import MultipleObjectMixin
from wkhtmltopdf.views import PDFTemplateView

from cart.cart import Cart
from product.filters import BlockFilter, ProductFilter
from product.forms import DraftPackageListItemForm, PackageListItemForm, PackageListItemEditForm, \
    PackageListItemMoveForm, PackageListImportForm
from public.views import OrderItemEditMixin, OrderItemDeleteMixin, ModalOptionsMixin, FilterListView, ModalEditMixin
from stock.models import Location, Stock, Warehouse
from public.utils import qs_to_dict, Package

from .models import Product, PackageList, DraftPackageList, DraftPackageListItem, Slab, Block, PackageListItem, \
    Category, Quarry, SlabYieldSet

from dal import autocomplete


class SalesOrderProductAutocomplete(autocomplete.Select2QuerySetView):
    model = Product
    model_field_name = 'block__name'

    def get_queryset(self):
        # qs = Product.objects.exclude(type='semi_slab')
        qs = super().get_queryset()
        wh_id = self.forwarded.get('warehouse')
        if wh_id:
            loc_childs = Warehouse.objects.get(pk=wh_id).get_main_location().get_child_list()
            qs = qs.filter(stock__location_id__in=loc_childs).distinct()
        if self.q:
            qs = qs.filter(block__name__contains=self.q)
        return qs


class BlockAutocompleteView(autocomplete.Select2QuerySetView):
    model = Block


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
    data = {'piece': piece, 'quantity': quantity, 'uom': product.get_uom(), 'm3': product.block.get_m3()}
    return JsonResponse(data)


class ProductAutocomplete(autocomplete.Select2QuerySetView):
    model = Product
    model_field_name = 'block__name'

    def get_queryset(self):
        # qs = Product.objects.exclude(type='semi_slab')
        loc_id = self.forwarded.get('location')  # production form 传来
        wh_id = self.forwarded.get('warehouse')  # sale_order form 传来
        type = self.forwarded.get('type', None)  # production form 传来
        qs = super().get_queryset()
        product_text = self.q
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
        # else:
        #     qs = qs.exclude(type='semi_slab')
        qs.distinct()
        # data = {str(p): {"id": p.id} for p in qs}
        return qs


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
    # else:
    #     qs = qs.exclude(type='semi_slab')
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


class CategoryListView(FilterListView):
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


class QuarryListView(FilterListView):
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
    #
    # def get_context_data(self, *args, **kwargs):
    #     context = super().get_context_data(*args, **kwargs)
    #     qs = super().get_queryset()
    #     total = {
    #         '编号':qs.annotate(block_count=Count('id')),
    #     }
    #     return context


class BlockDetailView(DetailView):
    model = Block


class ProductListView(FilterListView):
    model = Product
    filter_class = ProductFilter


class ProductDetailView(DetailView):
    model = Product


class SaleOrderListView(DetailView, MultipleObjectMixin):
    model = None
    template_name = 'product/product_sales_order.html'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        qs = self.object.sales_order_item.all()
        return super().get_context_data(object_list=qs, **kwargs)


class OriginalStockTraceView(DetailView, MultipleObjectMixin):
    model = Block
    template_name = 'product/block_original_stock_trace.html'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        qs = self.object.get_stock_trace_all()
        return super().get_context_data(object_list=qs, **kwargs)


class BlockSaleOrderListView(SaleOrderListView):
    model = Block


class ProductSaleOrderListView(SaleOrderListView):
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        state = self.request.GET.get('state')
        self.object = self.get_object()
        # 先把旧（库存）的码单slab取出
        old_slabs_ids = self.object.from_package_list.items.all().values_list('slab__id', flat=True)
        now_slabs_ids = self.object.items.values_list('slab__id', flat=True)

        slabs = Slab.objects.filter(id__in=set(now_slabs_ids) | set(old_slabs_ids))
        package = Package(self.object.product, slabs)
        add_new = True if state == 'draft' else False
        data = {'object': self.object, 'package': package, 'old_slabs_ids': old_slabs_ids,
                'now_slabs_ids': now_slabs_ids, 'add_new': add_new,
                'state': state}
        context.update(data)
        return context

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        slab_list = self.request.POST.getlist('select')
        self.object.update(self.object, slab_list)
        data = {'state': 'ok'}
        return JsonResponse(data)


# 库存盘点码单（新建）显示
class InventoryOrderNewItemPackageListDetailView(PackageListDetail):
    template_name = 'product/inventory_package_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        context.update(data)
        return context


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


class PackageListImportView(TemplateView):
    model = PackageList
    form_class = PackageListImportForm
    template_name = 'item_form.html'

    def get_context_data(self, **kwargs):
        if self.request.method == 'GET':
            kwargs['form'] = self.form_class()
        return super().get_context_data(**kwargs)

    def import_data(self, file):
        wb = xlrd.open_workbook(file_contents=file.read())
        table = wb.sheets()[0]
        part_1_2 = (12, 33)
        part_3_4 = (39, 60)
        part_5_6 = (66, 87)
        part_7_8 = (93, 114)
        left = (0, 7)
        right = (9, 16)
        next = (None, None)
        order_list = [part_1_2, part_3_4, part_5_6, part_7_8]
        result_lst = []
        part_number = 0
        names = ['line', 'long', 'height', 'kl1', 'kh1', 'kl2', 'kh2', 'part_number']
        for part in order_list:
            lr_count = 0
            for lr in [left, right]:
                part_number += 1
                # if lr[0] is None:
                #     continue
                lr_count += 1
                start, stop = part
                start_col, stop_col = lr
                for row in range(start, stop):
                    if not table.cell(row, start_col + 1).value:
                        break
                    line = table.row_values(row, start_col, stop_col)
                    line.append(part_number)
                    slab = {n: l if l else None for n, l in zip(names, line)}
                    result_lst.append(slab)
                if lr_count % 2 == 0:
                    continue
        slab_id_list = []
        try:
            for data in result_lst:
                slab = Slab(**data)
                slab.save()
                slab_id_list.append(slab.id)
            self.object.update(self.object, slab_id_list)
            return True, '成功'
        except Exception as e:
            return False, '导入码单数据不正确'

    @transaction.atomic()
    def post(self, *args, **kwargs):
        form = self.form_class(self.request.POST, self.request.FILES)
        self.object = PackageList.objects.get(pk=kwargs['pk'])
        sid = transaction.savepoint()
        msg = ''
        if form.is_valid():
            # 创建数据库事务保存点
            file = self.request.FILES.get('excel_file')
            is_done, msg = self.import_data(file)
            msg += '导入码单'
            if is_done:
                messages.success(self.request, msg)
                return JsonResponse({'state': 'ok', 'msg': msg})
            # 回滚数据库到保存点
            transaction.savepoint_rollback(sid)
            messages.error(self.request, msg)
        return self.render_to_response({'form': form, 'msg': msg})


# 码单item添加
class PackageListItemCreateView(OrderItemEditMixin):
    model = PackageListItem
    form_class = PackageListItemForm


# 码单item编辑
class PackageListItemEditView(OrderItemEditMixin):
    model = PackageListItem
    form_class = PackageListItemEditForm


# 删除码单所选item
class PackageListItemDeleteView(ModalOptionsMixin):
    model = PackageList
    form_class = PackageListItemMoveForm

    def get_success_url(self):
        path = self.request.META.get('HTTP_REFERER')
        return path

    def get_options(self):
        select_slab_ids = self.request.GET.getlist('select')
        if select_slab_ids:
            return (('do_yes', '是'), ('do_no', '否'))
        return (('nothing', '没有选择到板材'),)

    def do_option(self, option):
        if option == 'do_yes':
            items_ids = self.request.POST.get('select_slab_ids')
            if items_ids:
                ids = items_ids.split(',')
                PackageListItem.objects.filter(id__in=ids).delete()
                self.object.save()
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
            return '没有选择到板材'
        return '确定删除所选  %s  项？' % (len(select_slab_ids))


# 移动到其他夹
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


# 刷新序号
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


# 打印pdf
class PackageListPdfView(BaseDetailView, PDFTemplateView):
    model = PackageList
    # template_name = 'product/package_list_pdf.html'
    header_template = 'product/pdf/header.html'
    template_name = 'product/pdf/package_list_pdf.html'
    footer_template = 'product/pdf/footer.html'

    show_content_in_browser = True

    # cmd_options = {
    #     'margin-top': '0',
    #     'margin-left': '0',
    #     'margin-bottom': '0',
    #     'margin-right': '0',
    # }

    def get_filename(self):
        self.object = self.get_object()
        return '%s(%s)-%spcs-%spart-%s%s.pdf' % (
            self.object.product.name, self.object.product.thickness, self.object.get_piece(), self.object.get_part(),
            self.object.get_quantity(), self.object.product.get_uom())


# 打印标签pdf
class PackageListSlabPdfView(BaseDetailView, PDFTemplateView):
    model = PackageList
    # template_name = 'product/package_list_pdf.html'
    # header_template = 'product/pdf/header.html'
    template_name = 'product/pdf/package_list_slab_pdf.html'
    # footer_template = 'product/pdf/footer.html'

    show_content_in_browser = True
    cmd_options = {
        'page-height': '15.2cm',
        'page-width': '10.2cm',
        'margin-top': '0',
        'margin-left': '0',
        'margin-bottom': '0',
        'margin-right': '0',
    }

    def get_context_data(self, **kwargs):
        from public.gen_barcode import GenBarcode
        self.object = self.get_object()
        kwargs['barcode'] = GenBarcode(self.object.product.name, barcode_type='code39').value
        print(kwargs['barcode'])
        return super().get_context_data(**kwargs)

    def get_filename(self):
        self.object = self.get_object()
        return '%s#_tag.pdf' % self.object.product.name


class SlabYieldListView(ListView):
    model = SlabYieldSet


class SlabYieldEditView(ModalEditMixin):
    model = SlabYieldSet
    fields = '__all__'
    category_id = None

    def get_category_id(self, **kwargs):
        if self.object:
            return self.object.category.id

        return kwargs.get('category_id')

    def dispatch(self, request, *args, **kwargs):
        if kwargs.get('pk'):
            self.object = self.get_object()
        else:
            self.object = None
        self.category_id = self.get_category_id(**kwargs)
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial.update({'category': self.category_id})
        return initial

    def get_form(self, form_class=None):
        f = super().get_form(form_class)
        f.fields['category'].widget = forms.HiddenInput()
        return f