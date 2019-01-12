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
    path('block_list', views.get_block_list, name='get_block_list'),
    path('product_list', views.get_product_list, name='get_product_list'),
    path('product_info', views.get_product_info, name='get_product_info'),
    path('package_list/<pk>/pdf/', views.PackageListPdfView.as_view(), name='package_pdf'),

]
urlpatterns += [
    path('package_list/draft/item/delete/<pk>/', views.DraftPackageListItemDeleteView.as_view(),
         name='package_list_draft_item_delete'),
    path('package_list/draft/item/create/<order_id>/', views.DraftPackageListItemEditView.as_view(),
         name='package_list_draft_item_create'),
    path('package_list/draft/item/edit/<pk>/', views.DraftPackageListItemEditView.as_view(),
         name='package_list_draft_item_edit'),
    path('package_list/draft/quick_create/', views.DraftPackageListQuickCreateView.as_view(),
         name='quick_create_draft_package_list'),
    path('package_list/draft/create/', views.DraftPackageListCreateView.as_view(), name='package_list_draft_create'),
    path('package_list/draft/<pk>/', views.DraftPackageListDetailView.as_view(), name='package_list_draft_detail'),
    path('get_draft_package_list_info', views.get_draft_package_list_info, name='get_draft_package_list_info'),
    path('draft_package_list', views.DraftPackageListView.as_view(), name='get_draft_package_list'),
    # --------------------------出入库码单
    path('out_order_package_list/<pk>/', views.OutOrderPackageListDetailView.as_view(),
         name='out_order_package_detail'),
    # --------------------------盘点码单
    path('inventory_order_package_list/<pk>/', views.InventoryOrderPackageListDetailView.as_view(),
         name='inventory_order_package_detail'),
    path('inventory_order_new_package_list/<pk>/', views.InventoryOrderNewItemPackageListDetailView.as_view(),
         name='inventory_order_new_package_detail'),

    # --------------------------回退操作库码单
    path('turn_back_order_package_list/<pk>/', views.TurnBackOrderPackageListDetailView.as_view(),
         name='turn_back_order_package_detail'),
    # --------------------------销售单创建 及 编辑 码单
    path('package_list/create/<app_label_lower>/<item_id>/<product_id>/<location_id>/',
         views.OrderItemPackageListCreateView.as_view(),
         name='order_item_package_create'),
    path('package_list/<pk>/<location_id>/',
         views.SaleOrderPackageListView.as_view(),
         name='sales_order_package_list'),
    # --------------------------生产码单打开
    path('package_list/production/<pk>/', views.ProductionOrderPackageListDetailView.as_view(),
         name='package_production_detail'),
    # --------------------------一般码单打开
    path('package_list/item/edit/<pk>/', views.PackageListItemEditView.as_view(),
         name='package_list_item_edit'),
    path('package_list/item/create/<order_id>/', views.PackageListItemCreateView.as_view(),
         name='package_list_item_create'),
    path('package_list_full_page/item/move/<pk>/', views.PackageListItemMoveView.as_view(),
         name='package_list_item_move'),
    path('package_list_full_page/item/delete/<pk>/', views.PackageListItemDeleteView.as_view(),
         name='package_list_item_delete'),
    path('package_list_full_page/update_line/<pk>/', views.PackageListItemLineUpdateView.as_view(),
         name='package_full_page_update_line'),
    path('package_list_full_page/<pk>/', views.PackageListFullPageView.as_view(), name='package_full_page'),
    path('package_list/<pk>/', views.PackageListDetail.as_view(), name='package_detail'),
    path('category/<pk>/update/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('category/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('category/<pk>', views.CategoryDetailView.as_view(), name='category_detail'),
    path('category/', views.CategoryListView.as_view(), name='category_list'),
    path('quarry/<pk>/update/', views.QuarryUpdateView.as_view(), name='quarry_update'),
    path('quarry/create/', views.QuarryCreateView.as_view(), name='quarry_create'),
    path('quarry/<pk>', views.QuarryDetailView.as_view(), name='quarry_detail'),
    path('quarry/', views.QuarryListView.as_view(), name='quarry_list'),
    path('block/<pk>/sales_order/', views.BlockSaleOrderListView.as_view(), name='block_sales_order_list'),
    path('block/<pk>/', views.BlockDetailView.as_view(), name='block_detail'),
    path('block/', views.BlockListView.as_view(), name='block_list'),
    path('product/<pk>/sales_order/', views.ProductSaleOrderListView.as_view(), name='product_sales_order_list'),
    path('product/<pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('product/', views.ProductListView.as_view(), name='product_list'),
]
