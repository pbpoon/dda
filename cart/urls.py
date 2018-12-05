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
    path('add/<product_id>/', views.cart_add, name='cart_add'),
    path('remove/<product_id>', views.cart_remove, name='cart_remove'),
    path('clean/', views.cart_clean, name='cart_clean'),
    path('detail/', views.cart_detail, name='cart_detail'),

]
