#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/10/30
from django.urls import path
from . import views

urlpatterns = [
    path('<invoice_id>/payment/<partner_id>/', views.PaymentEditView.as_view(), name='payment_create_from_invoice'),
    path('payment/edit/<pk>/', views.PaymentEditView.as_view(), name='payment_edit'),
    path('payment/<pk>/', views.PaymentDetailView.as_view(), name='payment_detail'),
    path('payment/', views.PaymentListView.as_view(), name='payment_list'),
    path('account/create/', views.AccountCreateView.as_view(), name='account_create'),
    path('account/<pk>/', views.AccountDetailView.as_view(), name='account_detail'),
    path('account/', views.AccountListView.as_view(), name='account_list'),
    path('assign/<int:invoice_id>/<int:payment_id>', views.AssignPaymentFormView.as_view(), name='assign_payment'),
    path('assign/delete/<int:assign_id>', views.AssignDeleteView.as_view(), name='assign_delete'),
    path('item/create/<order_id>/', views.InvoiceItemEditView.as_view(), name='invoice_item_create'),
    path('item/delete/<pk>/', views.InvoiceItemDeleteView.as_view(), name='invoice_item_delete'),
    path('item/edit/<pk>/', views.InvoiceItemEditView.as_view(), name='invoice_item_edit'),
    path('<pk>/quick-assign-undercharge-payment/', views.QuickInvoiceAssignUnderchargePayment.as_view(),
         name='invoice_quick_assign_undercharge_payment'),
    path('<pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('', views.InvoiceListView.as_view(), name='invoice_list'),
]
