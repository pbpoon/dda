from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from .models import Partner


class PartnerListView(ListView):
    model = Partner


class PartnerDetailView(DetailView):
    model = Partner


class PartnerCreateView(CreateView):
    model = Partner
    fields = '__all__'


class PartnerUpdateView(UpdateView):
    model = Partner
    fields = '__all__'