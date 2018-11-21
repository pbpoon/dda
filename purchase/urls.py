#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/10/30
from django.urls import path
from . import views

urlpatterns = [
    path('edit_order_item/', views.PurchaseOrderItemEditView.as_view(), name='purchase_order_edit_item'),
    path('purchase_order_item_create/', views.PurchaseOrderItemCreateView.as_view(), name='purchase_order_item_create'),
    path('order/create/step/one/', views.PurchaseOrderCreateViewStepOne.as_view(), name='purchase_order_create_one'),
    path('order/create/step/two/', views.PurchaseOrderCreateViewStepTwo.as_view(), name='purchase_order_create_two'),
    path('order/create/', views.PurchaseOrderCreateView.as_view(), name='purchase_order_create'),
    path('order/<pk>/', views.PurchaseOrderDetailView.as_view(), name='purchase_order_detail'),
    path('order/', views.PurchaseOrderListView.as_view(), name='purchase_order_list'),
]