#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/10/30
from django.urls import path
from . import views

urlpatterns = [
    path('get_partner_info/', views.get_partner_info, name='get_partner_info'),
    path('get_partner_list/', views.get_partner_list, name='get_partner_list'),
    path('get_address/', views.get_address, name='get_address'),
    path('import_data/', views.ImportView.as_view(), name='import_data'),
    path('<pk>/update/', views.PartnerUpdateView.as_view(), name='partner_update'),
    path('company/update/<pk>/', views.MainInfoUpdateView.as_view(), name='company_update'),
    path('company/create/', views.MainInfoCreateView.as_view(), name='company_create'),
    path('company/<pk>/', views.MainInfoDetailView.as_view(), name='company_detail'),
    path('company', views.MainInfoView.as_view(), name='company'),
    path('create/', views.PartnerCreateView.as_view(), name='partner_create'),
    path('<pk>/', views.PartnerDetailView.as_view(), name='partner_detail'),
    path('', views.PartnerListView.as_view(), name='partner_list'),
]