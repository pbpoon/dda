import operator
from functools import reduce

from dal import autocomplete
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, FormView

from partner.forms import MainInfoForm
from public.permissions_mixin_views import DynamicPermissionRequiredMixin
from .models import Partner, Province, City, MainInfo


class ProvinceAutocomplete(autocomplete.Select2QuerySetView):
    model = Province

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(name__contains=self.q)
        return qs


class CustomerCompanyAutocompleteView(autocomplete.Select2QuerySetView):
    model = Partner

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(type='customer', is_company=True)


class CityAutocomplete(autocomplete.Select2QuerySetView):
    model = City

    def get_queryset(self):
        qs = super().get_queryset()
        prov = self.forwarded.get('province', None)
        if prov:
            qs = qs.filter(code=prov)
        if self.q:
            qs = qs.filter(name__contains=self.q)
        return qs


class PartnerCityAutocomplete(autocomplete.Select2QuerySetView):
    model = City

    def get_queryset(self):
        qs = super().get_queryset()
        prov = self.forwarded.get('partner_province', None)
        if prov:
            qs = qs.filter(code=prov)
        if self.q:
            qs = qs.filter(name__contains=self.q)
        return qs


class MainInfoEditMixin(DynamicPermissionRequiredMixin):
    model = MainInfo
    form_class = MainInfoForm
    template_name = 'form.html'

    def handle_no_permission(self):
        path = self.request.META.get('HTTP_REFERER')
        return HttpResponse(render_to_string('no_permissions.html', {'return_path': path}))


class MainInfoCreateView(MainInfoEditMixin, CreateView):
    pass


class MainInfoUpdateView(MainInfoEditMixin, UpdateView):
    pass


class MainInfoDetailView(DynamicPermissionRequiredMixin, DetailView):
    model = MainInfo


class MainInfoView(DynamicPermissionRequiredMixin, View):
    model = MainInfo

    def dispatch(self, request, *args, **kwargs):
        try:
            company = MainInfo.objects.get(pk=1)
            return redirect(reverse('company_detail', kwargs={'pk': company.id}))
        except ObjectDoesNotExist:
            return redirect(reverse('company_create'))


class PartnerListView(ListView):
    model = Partner


class PartnerDetailView(DetailView):
    model = Partner


class PartnerCreateView(CreateView):
    model = Partner
    fields = '__all__'
    template_name = 'form.html'


class PartnerUpdateView(UpdateView):
    model = Partner
    fields = '__all__'
    template_name = 'form.html'


def get_address(request):
    prov_id = request.GET.get('prov')
    # city_id = request.GET.get('city')
    data = {}
    # {id: id, name: name, area: {id, name}}
    if prov_id:
        qs = City.objects.filter(code=prov_id)
        data = {c.id: {'id': c.id, 'name': c.name} for c in qs}
    return JsonResponse(data)


def get_partner_list(request):
    prov_id = request.POST.get('province')
    city_id = request.POST.get('city')
    q = request.POST.get('partner_autocomplete')
    lst = []
    if q:
        for key in ['name__contains', 'phone__contains', 'company__name__contains', 'company__phone__contains', ]:
            q_obj = Q(**{key: q})
            lst.append(q_obj)
    qs = Partner.objects.filter(reduce(operator.or_, lst))
    if prov_id:
        qs = qs.filter(province_id=prov_id)
        if city_id:
            qs = qs.filter(city_id=city_id)
    if qs.count() > 10:
        qs = qs[0:10]
    data = {str(p) + p.get_address() + p.phone: {'id': p.id, 'image': None} for p in qs}
    return JsonResponse(data, safe=False)


def get_partner_info(request):
    partner_id = request.POST.get('partner_id')
    data = {}
    if partner_id:
        partner = Partner.objects.get(pk=partner_id)
        data = {'province': partner.province.code, 'city': partner.city.id}
    return JsonResponse(data)
