import operator
from functools import reduce
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, FormView

from partner.forms import MainInfoForm
from public.forms import AddExcelForm
from public.permissions_mixin_views import DynamicPermissionRequiredMixin
from public.utils import ImportData
from .models import Partner, Province, City, MainInfo


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


class ImportView(FormView):
    """
    导入省份，城市数据
    """
    data_type = 'city'
    template_name = 'form.html'
    form_class = AddExcelForm

    @transaction.atomic()
    def form_valid(self, form):
        f = form.files.get('file')

        model = Province if self.data_type == 'sheng' else City
        import_data = ImportData(f, data_type='city').data
        companys = self.format_to_company(import_data)
        for i in companys:
            data = {'name': i['company'],
                    'is_company': True,
                    'province': self.get_province(i),
                    'city': self.get_city(i),
                    'phone': i['phone'],
                    'type': 'customer',
                    'entry': self.request.user
                    }
            Partner.objects.create(**data)
        for i in import_data:
            data = {'name': i['name'],
                    'company': self.get_company(i),
                    'province': self.get_province(i),
                    'city': self.get_city(i),
                    'phone': i['phone'],
                    'type': 'customer',
                    'entry': self.request.user
                    }
            # data = {'id': i['id'],
            #         'code': i['provinceID'],
            #         'name': i['province']}
            Partner.objects.get_or_create(**data)

        return HttpResponse('0k')

    def get_province(self, i):
        if i['province']:
            return Province.objects.get(pk=i['province'])
        return None

    def get_city(self, i):
        if i['city']:
            return City.objects.get(pk=i['city'])
        return None

    def get_company(self, c):
        cc = None
        if c['company']:
            cc = Partner.objects.filter(is_company=True, name=c['company'])[0]
        return cc

    def format_to_company(self, data):
        return [i for i in data if i['company']]


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
