#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/10/30
from django.urls import path
from . import views

urlpatterns = [
    path('<invoice_id>/payment/<partner_id>', views.PaymentCreateView.as_view(), name='payment_create'),
    path('account/<pk>', views.AccountDetailView.as_view(), name='account_detail'),
    path('account/create/', views.AccountCreateView.as_view(), name='account_create'),
    path('account/', views.AccountListView.as_view(), name='account_list'),
    path('assign/<int:invoice_id>/<int:payment_id>', views.AssignPaymentFormView.as_view(), name='assign_payment'),
    path('assign/delete/<int:assign_id>', views.AssignDeleteView.as_view(), name='assign_delete'),
    path('<pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('', views.InvoiceListView.as_view(), name='invoice_list'),
]
