#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/10/30
from django.urls import path
from . import views

urlpatterns = [
    # ------------------------------------------------kes order
    path('move_order/item/delete/<pk>', views.MoveLocationOrderItemDeleteView.as_view(), name='move_location_order_delete'),
    path('move_order/create/', views.MoveLocationOrderCreateView.as_view(), name='move_location_order_create'),
    path('move_order/item/edit/', views.MoveLocationOrderItemEditView.as_view(), name='move_location_order_item_edit'),
    path('move_order/update/<pk>/', views.MoveLocationOrderUpdateView.as_view(), name='move_location_order_update'),
    path('move_order/<pk>/', views.MoveLocationOrderDetailView.as_view(), name='move_location_order_detail'),
    path('move_order/', views.MoveLocationOrderListView.as_view(), name='move_location_order_list'),
    # ------------------------------------------------block check in order

    path('block_check_in/create/<int:purchase_order_id>', views.BlockCheckInOrderCreateView.as_view(),
         name='block_check_in_create'),
    path('block_check_in/<int:pk>/<int:purchase_order_id>', views.BlockCheckInOrderUpdateView.as_view(),
         name='block_check_in_update'),
    path('block_check_in/<int:pk>/', views.BlockCheckInOrderDetailView.as_view(), name='block_check_in_detail'),

    path('block_check_in/item/edit/', views.BlockCheckInOrderItemEditView.as_view(), name='block_check_in_item_edit'),
    path('block_check_in/item/delete/<pk>', views.BlockCheckInOrderItemDeleteView.as_view(),
         name='block_check_in_item_delete'),
    path('block_check_in/', views.BlockCheckInOrderListView.as_view(), name='block_check_in_list'),

    # ------------------------------------------------kes order
    path('kes_order/produce_item/edit/', views.KesOrderProduceItemEditView.as_view(),
         name='kes_order_produce_item_edit'),
    path('kes_order/produce_item/delete/<pk>', views.KesOrderProduceItemDeleteView.as_view(),
         name='kes_order_produce_item_delete'),
    path('kes_order/raw_item/delete/<pk>', views.KesOrderRawItemDeleteView.as_view(), name='kes_order_raw_item_delete'),
    path('kes_order/raw_item/edit/', views.KesOrderRawItemEditView.as_view(), name='kes_order_raw_item_edit'),
    path('kes_order/update/<pk>', views.KesOrderUpdateView.as_view(), name='kes_order_update'),
    path('kes_order/create/', views.KesOrderCreateView.as_view(), name='kes_order_create'),
    path('kes_order/<pk>/', views.KesOrderDetailView.as_view(), name='kes_order_detail'),
    path('kes_order/', views.KesOrderListView.as_view(), name='kes_order_list'),
    # ------------------------------------------------kes order
    path('slab_check_in/item/edit/', views.SlabCheckInOrderItemEditView.as_view(), name='slab_check_in_item_edit'),
    path('slab_check_in/create/', views.SlabCheckInOrderCreateView.as_view(), name='slab_check_in_create'),
    path('slab_check_in/update/<pk>/', views.SlabCheckInOrderUpdateView.as_view(), name='slab_check_in_update'),
    path('slab_check_in/<pk>/', views.SlabCheckInOrderDetailView.as_view(), name='slab_check_in_detail'),
    path('slab_check_in/', views.SlabCheckInOrderListView.as_view(), name='slab_check_in_list'),
]
