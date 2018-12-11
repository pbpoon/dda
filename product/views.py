from django.apps import apps
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, HttpResponse
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import ListView, DetailView, CreateView

from cart.cart import Cart
from product.forms import DraftPackageListItemForm
from public.views import OrderItemEditMixin, OrderItemDeleteMixin
from stock.models import Location, Stock, Warehouse
from public.utils import qs_to_dict, Package

from .models import Product, PackageList, DraftPackageList, DraftPackageListItem, Slab
from django.core import serializers


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

    if wh_id:
        loc_id = Warehouse.objects.get(pk=wh_id).get_main_location().id
        loc_childs = Location.objects.get(pk=loc_id).child.all()
        loc_id = [loc_id, ]
        if loc_childs:
            loc_id = [c.id for c in loc_childs].append(loc_id)
    if type:
        qs = Product.objects.filter(stock__location_id__in=loc_id, type=type)
    else:
        qs = Product.objects.filter(stock__location_id__in=loc_id).exclude(type='semi_slab')
    product_text = request.POST.get('product_autocomplete')
    if product_text:
        qs.filter(block__name__icontains=product_text)
    data = {str(p.name) + p.get_type_display(): {"id": p.id} for p in qs}
    return JsonResponse(data, safe=False)


class ProductListView(ListView):
    model = Product


class ProductDetailView(DetailView):
    model = Product


class DraftPackageListView(ListView):
    model = DraftPackageList
    template_name = 'choice_package_list.html'


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


class DraftPackageListCreateView(CreateView):
    model = DraftPackageList
    template_name = "form.html"
    fields = ('name', 'entry')

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
    template_name = 'package_list.html'

    def get_state_draft_slabs(self):
        slabs = [item for stock in self.object.product.stock.all() for item in
                 stock.items.all().order_by('part_number', 'line')]
        return slabs

    def get(self, *args, **kwargs):
        state = self.request.GET.get('state')
        self.object = self.get_object()

        slabs = [item.slab for item in self.object.items.all().order_by('part_number', 'line')]
        package_slabs_ids = [s.get_slab_id() for s in slabs]

        if state == 'draft':
            slabs = self.get_state_draft_slabs()
        package = Package(self.object.product, slabs)

        cart = Cart(self.request)
        # edit_url = self.object.get_absolute_url
        # 'edit_url': edit_url,
        data = {'package': package, 'cart': cart, 'package_slabs_ids': package_slabs_ids,
                'state': state}
        return HttpResponse(render_to_string(self.template_name, data))

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        slab_list = self.request.POST.getlist('select')
        package = self.object.update(self.object, slab_list)
        return JsonResponse({'state': 'ok'})


# 提货单的码单显示
class OutOrderPackageListDetailView(PackageListDetail):

    def get_state_draft_slabs(self):
        slabs = [item.slab for item in self.object.from_package_list.items.filter(slab__stock__isnull=False)]
        return slabs


class OrderItemPackageListCreateView(View):
    template_name = 'package_list.html'

    def get(self, *args, **kwargs):
        location_id = self.kwargs.get('location_id')
        product_id = self.kwargs.get('product_id')
        stock = Stock.objects.filter(product_id=product_id, product__type='slab', location_id=location_id)
        slabs = [slab for s in stock for slab in s.items.filter(is_reserve=False)]
        package = Package(Product.objects.get(pk=product_id), slabs)
        package_slabs_ids = None
        data = {'package': package, 'package_slabs_ids': package_slabs_ids, 'state': 'draft'}
        return HttpResponse(render_to_string(self.template_name, data))

    def post(self, *args, **kwargs):
        slab_list = self.request.POST.getlist('select')
        product_id = self.kwargs.get('product_id')
        app_label_lower = self.kwargs.get('app_label_lower')
        app_label, model_name = app_label.split('.')
        package = PackageList.make_package_from_list(product_id, slab_list)
        item = apps.get_model(app_label=app_label, model_name=model_name).objects.get(pk=self.kwargs.get('item_id'))
        item.package_list = package
        item.piece = package.get_piece()
        item.quantity = package.get_quantity()
        item.save()
        return JsonResponse({'state': 'ok'})
