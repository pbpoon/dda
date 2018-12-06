from django.http import JsonResponse
from django.shortcuts import get_object_or_404, HttpResponse
from django.template.loader import render_to_string
from django.views.generic import ListView, DetailView, CreateView

from cart.cart import Cart
from product.forms import DraftPackageListItemForm
from public.views import OrderItemEditMixin, OrderItemDeleteMixin
from stock.models import Location
from public.utils import qs_to_dict, Package

from .models import Product, PackageList, DraftPackageList, DraftPackageListItem, Slab


def get_product_info(request):
    product_id = request.GET.get('product')
    location_id = request.GET.get('location')
    product = get_object_or_404(Product, pk=product_id)
    location = get_object_or_404(Location, pk=location_id)
    piece, quantity = product.get_available(location=location)

    data = {'piece': piece, 'quantity': quantity}
    return JsonResponse(data)


def get_product_list(request):
    loc_id = request.GET.get('location')
    loc_childs = Location.objects.get(pk=loc_id).child.all()
    if loc_childs:
        loc_id = [c.id for c in loc_childs].append(loc_id)
    products = Product.objects.filter(stock__location_id__in=loc_id)
    data = qs_to_dict(products)
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
        data = {'status': 'success',
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


class PackageListDetail(DetailView):
    model = PackageList
    template_name = 'package_list.html'

    # context_object_name = 'package'

    def get(self, *args, **kwargs):
        state = self.request.GET.get('state')
        self.object = self.get_object()

        slabs = [item.slab for item in self.object.items.all().order_by('part_number', 'line')]
        package_slabs_ids = [s.get_slab_id() for s in slabs]

        if state == 'draft':
            slabs = [item for stock in self.object.product.stock.all() for item in
                     stock.items.all().order_by('part_number', 'line')]
        package = Package(self.object.product, slabs)

        cart = Cart(self.request)
        edit_url = self.object.get_absolute_url
        data = {'package': package, 'cart': cart, 'package_slabs_ids': package_slabs_ids, 'edit_url': edit_url,
                'state': state}
        return HttpResponse(render_to_string(self.template_name, data))

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        slab_list = self.request.POST.getlist('select')
        package = self.object.update(self.object, slab_list)
        return JsonResponse({'state': 'ok'})


class SalseOrderPackageListDetailView(DetailView):
    model = Product
    template_name = 'package_list.html'

    def get(self, *args, **kwargs):
        state = self.request.GET.get('state')
        self.object = self.get_object()

        slabs = self.object.items.all().order_by('part_number', 'line')
        package_slabs_ids = [s.get_slab_id() for s in slabs]

        if state == 'draft':
            slabs = [item for stock in self.object.product.stock.all() for item in
                     stock.items.all().order_by('part_number', 'line')]
        package = Package(self.object.product, slabs)

        cart = Cart(self.request)
        edit_url = self.object.get_absolute_url
        data = {'package': package, 'cart': cart, 'package_slabs_ids': package_slabs_ids, 'edit_url': edit_url,
                'state': state}
        return HttpResponse(render_to_string(self.template_name, data))

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        slab_list = self.request.POST.getlist('select')
        package = self.object.update(self.object, slab_list)
        return JsonResponse({'state': 'ok'})
