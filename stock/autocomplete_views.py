#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2019/1/21
import operator
from functools import reduce

import six
from dal import autocomplete
from django.db.models import Q
from django.utils.html import format_html

from .models import Location


class InvOrderLocationAutocompleteView(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = Location.objects.filter(usage='internal')
        loc = self.forwarded.get('old_location', None)
        if loc:
            wh = Location.objects.get(pk=loc).warehouse
            qs = qs.filter(warehouse=wh)
        if self.q:
            lst = []
            for key in ['name__contains', 'warehouse__name__contains']:
                q_obj = Q(**{key: self.q})
                lst.append(q_obj)
            qs = qs.filter(reduce(operator.or_, lst))
        return qs


class MoveOrderLocationAutocompleteView(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = Location.objects.filter(usage='internal')
        wh = self.forwarded.get('warehouse', None)
        if wh:
            qs = qs.filter(warehouse__id=wh)
        if self.q:
            lst = []
            for key in ['name__contains', 'warehouse__name__contains']:
                q_obj = Q(**{key: self.q})
                lst.append(q_obj)
            qs = qs.filter(reduce(operator.or_, lst))
        return qs


class MoveOrderLocationDestAutocompleteView(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = Location.objects.filter(usage='internal')
        wh = self.forwarded.get('warehouse_dest', None)
        if wh:
            qs = qs.filter(warehouse__id=wh)
        if self.q:
            lst = []
            for key in ['name__contains', 'warehouse__name__contains']:
                q_obj = Q(**{key: self.q})
                lst.append(q_obj)
            qs = qs.filter(reduce(operator.or_, lst))
        return qs
