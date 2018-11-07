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
    path('block_check_in/', views.BlockCheckInOrderListView.as_view(), name='block_check_in_list'),
]
