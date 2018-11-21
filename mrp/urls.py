#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/10/30
from django.urls import path
from . import views

urlpatterns = [
    path('block_check_in/create/<int:purchase_order_id>', views.BlockCheckInOrderCreateView.as_view(),
         name='block_check_in_create'),
    path('block_check_in/<int:pk>/<int:purchase_order_id>', views.BlockCheckInOrderUpdateView.as_view(),
         name='block_check_in_update'),
    path('block_check_in/<int:pk>/', views.BlockCheckInOrderDetailView.as_view(), name='block_check_in_detail'),
    path('kes_order/create/step2/<int:kes_order_id>', views.KesOrderCreateStep2View.as_view(),
         name='kes_order_create_step2'),
    path('kes_order/create/step3/<int:kes_order_id>', views.KesOrderCreateStep3View.as_view(),
         name='kes_order_create_step3'),
    path('kes_order/delete/raw_item/<pk>', views.KesOrderDeleteRawItem.as_view(), name='kes_order_delete_raw_item'),
    path('kes_order/create/', views.KesOrderCreateView.as_view(), name='kes_order_create'),
    path('kes_order/<pk>/', views.KesOrderDetailView.as_view(), name='kes_order_detail'),
    path('kes_order/', views.KesOrderListView.as_view(), name='kes_order_list'),
    path('block_check_in/', views.BlockCheckInOrderListView.as_view(), name='block_check_in_list'),
]
