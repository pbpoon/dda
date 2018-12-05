#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/10/30
from django.urls import path
from . import views

urlpatterns = [
    # ------------------------------------------------kes order
    path('move_order/item/delete/<pk>', views.MoveLocationOrderItemDeleteView.as_view(),
         name='move_location_order_delete'),
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

    # ------------------------------------------------production order
    path('production/produce_item/delete/<pk>', views.ProductionOrderProduceItemDeleteView.as_view(), name='production_produce_item_delete'),
    path('production/produce_item/edit/', views.ProductionOrderProduceItemEditView.as_view(), name='production_produce_item_edit'),
    path('production/raw_item/delete/<pk>', views.ProductionOrderRawItemDeleteView.as_view(), name='production_raw_item_delete'),
    path('production/raw_item/edit/', views.ProductionOrderRawItemEditView.as_view(), name='production_raw_item_edit'),
    path('production/update/<pk>/', views.ProductionOrderUpdateView.as_view(), name='production_update'),
    path('production/create/', views.ProductionOrderCreateView.as_view(), name='production_create'),
    path('production/<pk>/', views.ProductionOrderDetailView.as_view(), name='production_detail'),
    path('production/', views.ProductionOrderListView.as_view(), name='production_list'),
    # ------------------------------------------------production type
    path('production_type/update/<pk>', views.ProductionTypeUpdateView.as_view(), name='production_type_update'),
    path('production_type/create/', views.ProductionTypeCreateView.as_view(), name='production_type_create'),
    path('production_type/<pk>/', views.ProductionTypeDetailView.as_view(), name='production_type_detail'),
    path('production_type/', views.ProductionTypeListView.as_view(), name='production_type_list'),
]
