#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2019/2/23
import django_filters
from django_filters.widgets import LinkWidget


class StateOrderFilter(django_filters.FilterSet):
    state = django_filters.ChoiceFilter(label='状态',
                                        choices=(('draft', '草稿'), ('confirm', '确认'), ('done', '完成'), ('cancel', '取消'),),
                                        widget=LinkWidget(attrs={'class': 'inline-ul'}))

