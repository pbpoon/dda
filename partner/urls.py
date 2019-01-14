#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/10/30
from django.urls import path
from . import views
from . import import_data_views

urlpatterns = [
    path('get_partner_info/', views.get_partner_info, name='get_partner_info'),
    path('get_partner_list/', views.get_partner_list, name='get_partner_list'),
    path('get_address/', views.get_address, name='get_address'),
    path('<pk>/update/', views.PartnerUpdateView.as_view(), name='partner_update'),
    path('company/update/<pk>/', views.MainInfoUpdateView.as_view(), name='company_update'),
    path('company/create/', views.MainInfoCreateView.as_view(), name='company_create'),
    path('company/<pk>/', views.MainInfoDetailView.as_view(), name='company_detail'),
    path('company', views.MainInfoView.as_view(), name='company'),
    path('create/', views.PartnerCreateView.as_view(), name='partner_create'),
    path('<pk>/', views.PartnerDetailView.as_view(), name='partner_detail'),
    path('', views.PartnerListView.as_view(), name='partner_list'),
]
# urlpatterns += [
#     path('import_data/partner/', import_data_views.ImportPartnerView.as_view(), name='import_partner_data'),
#     path('import_data/slab/', import_data_views.ImportSlabView.as_view(), name='import_slab_data'),
#     path('import_data/stock/', import_data_views.ImportStockView.as_view(), name='import_stock_data'),
#     path('import_data/block/', import_data_views.ImportBlockView.as_view(), name='import_block_data'),
#     path('import_data/trace/', import_data_views.ImportStockTraceView.as_view(), name='import_trace_data'),
# ]
