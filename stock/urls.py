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
    # path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    #导入 admin。widget需要的url
    path('stock/', views.StockListView.as_view(), name='stock_list'),
    path('location/update/<pk>', views.LocationUpdateView.as_view(), name='location_edit'),
    path('location/create/<int:warehouse_id>', views.LocationCreateView.as_view(), name='location_create'),
    path('warehouse/update/<pk>/', views.WarehouseUpdateView.as_view(), name='warehouse_update'),
    path('warehouse/create/', views.WarehouseCreateView.as_view(), name='warehouse_create'),
    path('warehouse/<pk>/', views.WarehouseDetailView.as_view(), name='warehouse_detail'),
    path('warehouse/', views.WarehouseListView.as_view(), name='warehouse_list'),
]
