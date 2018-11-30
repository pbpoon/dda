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
    path('package_list/draft/item/delete/<pk>', views.DraftPackageListItemDeleteView.as_view(), name='package_list_draft_item_delete'),
    path('package_list/draft/item/edit/', views.DraftPackageListItemEditView.as_view(), name='package_list_draft_item_edit'),
    path('package_list/draft/<pk>', views.DraftPackageListDetailView.as_view(), name='package_list_draft_detail'),
    path('package_list/draft/create/', views.DraftPackageListCreateView.as_view(), name='package_list_draft_create'),
    path('product_list', views.get_product_list, name='get_product_list'),
    path('product_info', views.get_product_info, name='get_product_info'),
    path('<pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('', views.ProductListView.as_view(), name='product_list'),
]
