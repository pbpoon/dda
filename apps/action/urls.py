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
    # path('auth/', views.WechatAuthView.as_view(), name='wechat_auth'),
    path('test/js-sdk/', views.TestJsSdkView.as_view(), name='wechat_test_jssdk'),
    path('scheme-push/', views.SchemeWxPush.as_view(), name='wechat_scheme_push'),
    path('payment/', views.WxPaymentView.as_view(), name='wechat_payment'),
    path('block_search/', views.WxBlockSearchView.as_view(), name='wechat_block_search'),
    path('', views.WxMainView.as_view(), name='wechat'),
]
