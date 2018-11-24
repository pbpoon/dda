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

    path('kes_order/produce_item/edit/', views.KesOrderProduceItemEditView.as_view(),
         name='kes_order_produce_item_edit'),
    path('kes_order/produce_item/delete/<pk>', views.KesOrderProduceItemDeleteView.as_view(),
         name='kes_order_produce_item_delete'),
    path('kes_order/raw_item/delete/<pk>', views.KesOrderRawItemDeleteView.as_view(), name='kes_order_raw_item_delete'),
    path('kes_order/raw_item/edit/', views.KesOrderRawItemEditView.as_view(), name='kes_order_raw_item_edit'),
    path('kes_order/create/', views.KesOrderCreateView.as_view(), name='kes_order_create'),
    path('kes_order/<pk>/', views.KesOrderDetailView.as_view(), name='kes_order_detail'),
    path('kes_order/', views.KesOrderListView.as_view(), name='kes_order_list'),
    path('block_check_in/', views.BlockCheckInOrderListView.as_view(), name='block_check_in_list'),
]
