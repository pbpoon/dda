import collections

from django import forms
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Sum
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views.generic.detail import BaseDetailView
from django.views.generic.edit import ModelFormMixin
from django.views.generic.list import MultipleObjectMixin
from wkhtmltopdf.views import PDFTemplateView

from cart.cart import Cart
from product.forms import PackageListItemMoveForm
from product.models import Slab, PackageList
from product.views import PackageListItemLineUpdateView
from public.forms import LocationForm
from public.permissions_mixin_views import DynamicPermissionRequiredMixin
from public.utils import Package
from public.views import OrderItemEditMixin, FilterListView, ModalEditMixin, ModalOptionsMixin
from public.widgets import SwitchesWidget
from stock.forms import SlabEditForm
from .models import Warehouse, Location, Stock
from .filters import StockFilter, WarehouseLocationFilter


class WarehouseListView(FilterListView):
    model = Warehouse


class WarehouseDetailView(DynamicPermissionRequiredMixin, DetailView, MultipleObjectMixin):
    model = Warehouse

    def get_context_data(self, **kwargs):
        items = self.object.locations.all()
        filter = WarehouseLocationFilter(self.request.GET, queryset=items)
        kwargs['filter'] = filter
        return super().get_context_data(object_list=filter.qs.distinct(), **kwargs)


class WarehouseEditMixin:
    model = Warehouse
    fields = '__all__'
    template_name = 'stock/form.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['is_production'].widget = SwitchesWidget()
        return form


class WarehouseCreateView(WarehouseEditMixin, CreateView):
    pass


class WarehouseUpdateView(WarehouseEditMixin, UpdateView):
    pass


class LocationEditMixin(DynamicPermissionRequiredMixin, ModelFormMixin, View):
    model = Location
    form_class = LocationForm
    template_name = 'item_form.html'

    def get_initial(self):
        initial = super().get_initial()
        self.warehouse = get_object_or_404(Warehouse, pk=self.kwargs.get('warehouse_id'))
        if self.warehouse:
            initial.update({'warehouse': self.warehouse.id})
        initial['usage'] = 'internal'
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.warehouse:
            form.fields['parent'].queryset = self.warehouse.get_main_location().get_child()
        return form

    def post(self, *args, **kwargs):
        self.object = self.get_object() if self.kwargs.get('pk') else None
        path = self.request.META.get('HTTP_REFERER')
        form = self.get_form()
        msg = '修改' if self.object else '添加'
        if form.is_valid():
            form.save()
            msg += '成功'
            messages.success(self.request, msg)
            # return redirect(path)
            return JsonResponse({'state': 'ok', 'url': path})
        msg += '失败'
        return HttpResponse(render_to_string(self.template_name, {'form': form, 'error': msg}))


class LocationCreateView(LocationEditMixin, CreateView):
    pass


class LocationUpdateView(DynamicPermissionRequiredMixin, UpdateView):
    model = Location
    form_class = LocationForm
    template_name = 'form.html'


class LocationListView(ListView):
    model = Location


class LocationDetailView(DynamicPermissionRequiredMixin, DetailView):
    model = Location


class StockListView(FilterListView):
    model = Stock
    paginate_by = 20
    filter_class = StockFilter
    ordering = ('-created',)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        qs = super().get_queryset()
        context.update(
            qs.aggregate(count_total=Count('product'), piece_total=Sum('piece'), quantity_total=Sum('quantity')))
        return context


class StockListPhotoView(StockListView):
    template_name = 'stock/stock_photo_list.html'

    def post(self, *args, **kwargs):
        if not self.request.POST.get('go'):
            return JsonResponse({'state': 'ok'})
        qs = super().get_queryset()[:20]
        block_ids = qs.values_list('product__block__id', flat=True)
        if not block_ids:
            return JsonResponse({'state': 'ok', 'inside': 'no', 'msg': '但前没有任何编号'})
        try:
            collect_block = self.request.user.collect_block
        except Exception as e:
            from account.models import UserCollectBlock
            collect_block = UserCollectBlock.objects.create(user=self.request.user)
        collect_block.block_list = list(block_ids)
        collect_block.save()
        return JsonResponse({'state': 'ok', 'inside': 'yes', 'msg': '已把当前编号添加到收藏(最多20个编号)'})


class StockChartsListView(FilterListView):
    model = Stock
    # paginate_by = 20
    filter_class = StockFilter
    template_name = 'stock/stock_charts_list.html'

    def get_charts_data(self, object_list):
        """
        按厚度 pie
        按仓位 pie
        按类型 clomn

        """
        loc = collections.defaultdict(lambda: 0)
        thick = collections.defaultdict(lambda: 0)
        type = collections.defaultdict(lambda: 0)
        for obj in object_list:
            loc[obj.location.warehouse] += int(obj.quantity)
            thick[obj.product.thickness] += int(obj.quantity)
            type[obj.product.get_type_display()] += int(obj.quantity)
        series = [{'name': '厚度规格占比',
                   'data': [{'name': str(thickness), 'y': thick[thickness]} for thickness in thick]}]
        series2 = [{'name': '仓库数量占比',
                    'data': [{'name': str(l), 'y': loc[l]} for l in loc]}]
        series3 = [{'name': '类型占比',
                    'data': [{'name': str(t), 'y': type[t]} for t in type]}]

        data = {'series': series,
                'series2': series2,
                'series3': series3}
        return data

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        qs = super().get_queryset()
        context.update(
            qs.aggregate(count_total=Count('product'), piece_total=Sum('piece'), quantity_total=Sum('quantity')))
        context.update(self.get_charts_data(qs))
        return context


class StockDetailView(DynamicPermissionRequiredMixin, DetailView):
    model = Stock
    template_name = 'stock/detail.html'

    def post(self, *args, **kwargs):
        slab_list = self.request.POST.getlist('select')
        product_id = self.request.POST.get('product')
        if slab_list:
            cart = Cart(self.request)
            cart.add(product_id, slab_id_list=slab_list)
            return JsonResponse({'state': 'ok'})


class StockSlabsView(DynamicPermissionRequiredMixin, DetailView):
    model = Stock
    template_name = 'stock/package_list.html'

    def get_context_data(self, **kwargs):
        product = self.object.product
        slabs = self.object.items.all()
        package = Package(product, slabs)
        kwargs['package'] = package
        return super().get_context_data(**kwargs)


class StockSlabsFullPageView(StockSlabsView):
    template_name = 'stock/packagelist_full_page.html'


class SlabsEditView(ModalEditMixin):
    model = Slab
    form_class = SlabEditForm


# 移动到其他夹
class StockSlabMoveView(ModalOptionsMixin):
    model = Stock
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
            Slab.objects.filter(id__in=ids).update(part_number=option)
        return True, ''

    def get_form(self):
        select_slab_ids = self.request.GET.getlist('select')
        items_ids = self.object.items.filter(id__in=select_slab_ids).values_list(
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
class StockSlabsLineUpdateView(PackageListItemLineUpdateView):
    model = Stock


# 打印pdf
class StockPackageListPdfView(BaseDetailView, PDFTemplateView):
    model = Stock
    context_object_name = 'object'
    # template_name = 'product/package_list_pdf.html'
    template_name = 'stock/pdf/package_list_pdf.html'
    header_template = 'stock/pdf/header.html'
    footer_template = 'stock/pdf/footer.html'

    show_content_in_browser = True

    # cmd_options = {
    #     'margin-top': '0',
    #     'margin-left': '0',
    #     'margin-bottom': '0',
    #     'margin-right': '0',
    # }
    def get_context_data(self, **kwargs):
        package = Package(self.object.product, self.object.items.all())
        kwargs['package'] = package
        return super().get_context_data(**kwargs)

    def get_filename(self):
        self.object = self.get_object()
        return '%s.pdf' % (self.object.product)


# 打印标签pdf
class StockPackageListSlabPdfView(BaseDetailView, PDFTemplateView):
    model = Stock
    context_object_name = 'object'
    template_name = 'stock/pdf/package_list_slab_pdf.html'

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
        kwargs['barcode'] = GenBarcode('%s' % self.object.product.name, barcode_type='code39').value
        product = self.object.product
        slabs = self.object.items.all()
        package = Package(product, slabs)
        kwargs['package'] = package
        return super().get_context_data(**kwargs)

    def get_filename(self):
        self.object = self.get_object()
        return '%s#_tag.pdf' % self.object.product.name
