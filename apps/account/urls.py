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
from django.contrib.auth import views as auth_views
from sales.views import UserSalesOrderListView
urlpatterns = [
    path('daily/<int:year>/<int:month>/<int:day>/', views.DayDailyView.as_view(), name='day_daily'),
    path('collect-block/<pk>/', views.CollectBlockUpdateView.as_view(), name='collect_block_update'),
    path('sales-order/', UserSalesOrderListView.as_view(template_name='account/sales_order_list.html'), name='user_sales_order_list'),
    path('collect-block-list/', views.UserCollectBlockListView.as_view(), name='collect_block_list'),
    path('collect-block-list/share/<str:string>', views.CollectBlockPhotoListView.as_view(), name='collect_block_share'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
]
