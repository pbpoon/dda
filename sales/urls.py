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
from django.urls import include
from . import views


urlpatterns = [
    path('order/item/delete/<pk>/', views.SalesOrderItemDeleteView.as_view(), name='sales_order_item_delete'),
    path('order/item/edit/<pk>/', views.SalesOrderItemEditView.as_view(), name='sales_order_item_edit'),
    path('order/item/edit/', views.SalesOrderItemEditView.as_view(), name='sales_order_item_create'),
    path('order/update/<pk>/', views.SalesOrderUpdateView.as_view(), name='sales_order_update'),
    path('order/quick/create/', views.SalesOrderQuickCreateView.as_view(), name='sales_order_quick_create'),
    path('order/create/', views.SalesOrderCreateView.as_view(), name='sales_order_create'),
    path('order/<pk>/', views.SalesOrderDetailView.as_view(), name='sales_order_detail'),
    path('order/', views.SalesOrderListView.as_view(), name='sales_order_list'),
]
