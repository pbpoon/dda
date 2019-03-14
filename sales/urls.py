"""stone URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views
from .filters import CustomerAutocomplete
urlpatterns = [
    path('order/pdf/<pk>/', views.OrderToPdfView.as_view(), name='sales_order_pdf'),
    path('order/item/delete/<pk>/', views.SalesOrderItemDeleteView.as_view(), name='sales_order_item_delete'),
    path('order/item/edit/<pk>/', views.SalesOrderItemEditView.as_view(), name='sales_order_item_edit'),
    path('order/item/create/<order_id>/', views.SalesOrderItemEditView.as_view(), name='sales_order_item_create'),
    path('order/<pk>/update/', views.SalesOrderUpdateView.as_view(), name='sales_order_update'),
    path('order/<pk>/delete/', views.SalesOrderDeleteView.as_view(), name='sales_order_delete'),
    path('order/quick/create/', views.SalesOrderQuickCreateView.as_view(), name='sales_order_quick_create'),
    path('order/create/<customer_id>', views.SalesOrderCreateByCustomerView.as_view(), name='sales_order_create_by_customer'),
    path('order/create/', views.SalesOrderCreateView.as_view(), name='sales_order_create'),
    path('order/invoice/options/<pk>/', views.SalesOrderInvoiceOptionsEditView.as_view(),
         name='sales_order_invoice_options'),
    path('order/charts/', views.SalesOrderChrtsView.as_view(), name='sales_order_charts_list'),
    path('order/month/', views.SalesOrderMonthListView.as_view(), name='sales_order_month_list'),
    path('order/<int:pk>/', views.SalesOrderDetailView.as_view(), name='sales_order_detail'),
    path('order/', views.SalesOrderListView.as_view(), name='sales_order_list'),
    path('customer/create/', views.CustomerCreateView.as_view(), name='customer_create'),
    path('customer/<pk>/delete/', views.CustomerDeleteView.as_view(), name='customer_delete'),
    path('customer/<pk>/update/', views.CustomerUpdateView.as_view(), name='customer_update'),
    path('customer/<pk>/', views.CustomerDetailView.as_view(), name='customer_detail'),
    path('customer-autocomplete/', CustomerAutocomplete.as_view(), name='customer_autocomplete'),
    path('customer/', views.CustomerListView.as_view(), name='customer_list'),
]
