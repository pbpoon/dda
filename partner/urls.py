#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/10/30
from django.urls import path
from . import views

urlpatterns = [
    path('<pk>/update/', views.PartnerUpdateView.as_view(), name='partner_update'),
    path('create/', views.PartnerCreateView.as_view(), name='partner_create'),
    path('<pk>/', views.PartnerDetailView.as_view(), name='partner_detail'),
    path('', views.PartnerListView.as_view(), name='partner_list'),
]