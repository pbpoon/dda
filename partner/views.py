import json

from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, FormView

from public.forms import AddExcelForm
from public.utils import ImportData
from .models import Partner, Province, City, Area


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

    def form_valid(self, form):
        f = form.files.get('file')

        model = Province if self.data_type == 'sheng' else City
        import_data = ImportData(f, data_type='sheng').data
        for i in import_data:
            # data = {'id': i['id'],
            #         'code': i['provinceID'],
            #         'name': i['province']}
            Province.objects.create(**i)
        return HttpResponse('0k')
