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

urlpatterns = [path('product_list', views.get_product_list, name='get_product_list'),
               path('product_info', views.get_product_info, name='get_product_info'), ]
urlpatterns += [
    path('package_list/draft/item/delete/<pk>/', views.DraftPackageListItemDeleteView.as_view(),
         name='package_list_draft_item_delete'),
    path('package_list/draft/item/create/<order_id>/', views.DraftPackageListItemEditView.as_view(),
         name='package_list_draft_item_create'),
    path('package_list/draft/item/edit/<pk>/', views.DraftPackageListItemEditView.as_view(),
         name='package_list_draft_item_edit'),
    path('package_list/draft/create/', views.DraftPackageListCreateView.as_view(), name='package_list_draft_create'),
    path('package_list/draft/<pk>/', views.DraftPackageListDetailView.as_view(), name='package_list_draft_detail'),
    path('get_draft_package_list_info', views.get_draft_package_list_info, name='get_draft_package_list_info'),
    path('draft_package_list', views.DraftPackageListView.as_view(), name='get_draft_package_list'),
    # --------------------------出入库码单
    path('out_order_package_list/<pk>/', views.OutOrderPackageListDetailView.as_view(),
         name='out_order_package_detail'),
    # --------------------------回退操作库码单
    path('turn_back_order_package_list/<pk>/', views.TurnBackOrderPackageListDetailView.as_view(),
         name='turn_back_order_package_detail'),
    # --------------------------销售单创建码单
    path('package_list/create/<app_label_lower>/<item_id>/<product_id>/<location_id>/',
         views.OrderItemPackageListCreateView.as_view(),
         name='order_item_package_create'),
    # --------------------------一般码单打开
    path('package_list/<pk>/', views.PackageListDetail.as_view(), name='package_detail'),
    path('block/<pk>/', views.BlockDetailView.as_view(), name='block_detail'),
    path('block/', views.BlockListView.as_view(), name='block_list'),
    path('<pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('', views.ProductListView.as_view(), name='product_list'),
]
