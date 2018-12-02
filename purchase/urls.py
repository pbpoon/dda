#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/10/30
from django.urls import path
from . import views

urlpatterns = [
    path('order/item/delete/<pk>', views.PurchaseOrderItemDeleteView.as_view(), name='purchase_order_item_delete'),
    path('order/item/edit/', views.PurchaseOrderItemEditView.as_view(), name='purchase_order_item_edit'),
    path('order/update/<pk>', views.PurchaseOrderUpdateView.as_view(), name='purchase_order_update'),
    path('order/create/', views.PurchaseOrderCreateView.as_view(), name='purchase_order_create'),
    path('order/<pk>/', views.PurchaseOrderDetailView.as_view(), name='purchase_order_detail'),
    path('order/', views.PurchaseOrderListView.as_view(), name='purchase_order_list'),
]