#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/10/30
from django.urls import path
from . import views

urlpatterns = [
    path('purchase_order_item_edit/', views.PurchaseOrderItemEditView.as_view(), name='import_block_edit'),
    path('order/create/step/one/', views.PurchaseOrderCreateViewSetpOne.as_view(), name='purchase_order_create_one'),
    path('order/create/step/two/', views.PurchaseOrderCreateViewSetpTwo.as_view(), name='purchase_order_create_two'),
    path('order/<pk>/', views.PurchaseOrderDetailView.as_view(), name='purchase_order_detail'),
    path('order/', views.PurchaseOrderListView.as_view(), name='purchase_order_list'),
]