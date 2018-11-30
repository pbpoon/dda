from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, HttpResponse
from django.views.generic import ListView, DetailView, CreateView

from product.forms import DraftPackageListItemForm
from public.views import OrderItemEditMixin, OrderItemDeleteMixin
from stock.models import Location
from utils import obj_to_dict, qs_to_dict

from .models import Product, Category, Slab, PackageList, DraftPackageList, DraftPackageListItem


def get_product_info(request):
    product_id = request.GET.get('value')
    product = get_object_or_404(Product, pk=product_id)
    data = obj_to_dict(product)
    if product.uom == 't':
        data['quantity'] = data['weight']
    else:
        data['quantity'] = data['m3']
    data['piece'] = 1
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
