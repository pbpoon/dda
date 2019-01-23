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
from . import autocomplete_views

urlpatterns = [
    path('location/create/<warehouse_id>/', views.LocationCreateView.as_view(), name='location_create'),
    path('location/update/<pk>/', views.LocationUpdateView.as_view(), name='location_edit'),
    path('location—autocomplete/', autocomplete_views.LocationAutocompleteView.as_view(),
         name='location_autocomplete'),
    path('warehouse/update/<pk>/', views.WarehouseUpdateView.as_view(), name='warehouse_update'),
    path('warehouse/create/', views.WarehouseCreateView.as_view(), name='warehouse_create'),
    path('warehouse/<pk>/', views.WarehouseDetailView.as_view(), name='warehouse_detail'),
    path('warehouse/', views.WarehouseListView.as_view(), name='warehouse_list'),
    path('slabs/<pk>/pdf-package/', views.StockPackageListPdfView.as_view(), name='stock_slabs_pdf'),
    path('slabs/<pk>/full/', views.StockSlabsFullPageView.as_view(), name='stock_slabs_detail_full'),
    path('slabs/<pk>/', views.StockSlabsView.as_view(), name='stock_slabs_detail'),
    path('slab/<pk>/edit/', views.SlabsEditView.as_view(), name='stock_slab_edit'),
    path('available/<pk>/slabs/move/', views.StockSlabMoveView.as_view(), name='stock_slabs_move'),
    path('available/<pk>/update_line/', views.StockSlabsLineUpdateView.as_view(), name='stock_slabs_update_line'),
    path('available/<pk>/', views.StockDetailView.as_view(), name='stock_detail'),
    path('available/', views.StockListView.as_view(), name='stock_list'),
]
