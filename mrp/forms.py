#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/11/5
from django import forms
from django.urls import reverse, reverse_lazy

from product.models import Product
from stock.models import Location
from .models import BlockCheckInOrder, KesOrderRawItem, KesOrderProduceItem, KesOrder, BlockCheckInOrderItem, \
    MoveLocationOrder, MoveLocationOrderItem, SlabCheckInOrder


class BlockCheckInOrderForm(forms.ModelForm):
    class Meta:
        model = BlockCheckInOrder
        exclude = ('location', 'location_dest')
        widgets = {
            'entry': forms.HiddenInput,
            'purchase_order': forms.HiddenInput,
            'order': forms.HiddenInput,
            'state': forms.HiddenInput,
        }


class BlockCheckInOrderItemForm(forms.ModelForm):
    class Meta:
        model = BlockCheckInOrderItem
        exclude = ('location', 'location_dest')
        widgets = {
            'order': forms.HiddenInput,
        }

    def __init__(self, *args, **kwargs):
        order = kwargs.pop('block_check_in_order')
        super(BlockCheckInOrderItemForm, self).__init__(*args, **kwargs)
        if kwargs.get('instance', None) is None:
            already_check_in_products = [i.product.id for i in order.purchase_order.items.filter(
                order__block_check_in_order__state__in=('confirm', 'done'))]
            already_check_in_products.extend([i.product.id for i in order.items.all()])
            products = [i.product.id for i in order.purchase_order.items.all() if
                        i.product.id not in already_check_in_products]
            qs = Product.objects.filter(id__in=products)
            url = reverse_lazy('get_product_info')
            self.fields['product'].queryset = qs
            self.fields['product'].widget.attrs = {
                'onchange': 'set_onchange({},"{}","quantity")'.format('this.value', url)}


class KesOrderForm(forms.ModelForm):
    class Meta:
        model = KesOrder
        exclude = ('order', 'location', 'location_dest', 'state')
        widgets = {
            'entry': forms.HiddenInput,
        }


class KesOrderRawItemForm(forms.ModelForm):
    class Meta:
        model = KesOrderRawItem
        exclude = ('location', 'location_dest')
        widgets = {
            'piece': forms.HiddenInput,
            'order': forms.HiddenInput,
        }

    def __init__(self, *args, **kwargs):
        kes_order = kwargs.pop('kes_order')
        super(KesOrderRawItemForm, self).__init__(*args, **kwargs)
        # 按order的原材料的type来筛选product的query_set
        if kwargs.get('instance', None):
            #如果是编辑状态，就把本荒料编号添加上
            qs = Product.objects.filter(id=kwargs.get('instance').product.id)
        elif kes_order and kes_order.items.all():
            # 如果是是新建状态，并且本order已经有原材料行，就把已经填写的原料的的产品剔出
            qs = Product.objects.filter(type='block', stock__isnull=False).exclude(
                pk__in=[int(item.product.id) for item in kes_order.items.all()])
        else:
            # 如果是完全新建状态，就直接按order的原材料的type来筛选product
            qs = Product.objects.filter(type='block', stock__isnull=False)
        # 把qs赋值到product的queryset
        self.fields['product'].queryset = qs
        # onchange的ajax取数据url
        url = reverse_lazy('get_product_info')
        self.fields['product'].widget.attrs = {
            'onchange': 'onchange_set_product_info({},"{}","quantity")'.format('this.value', url)}


class KesOrderProduceItemForm(forms.ModelForm):
    class Meta:
        model = KesOrderProduceItem
        fields = ('order', 'raw_item', 'thickness', 'piece')
        widgets = {
            'order': forms.HiddenInput,
            'raw_item': forms.HiddenInput,
        }

    def clean_thickness(self):
        thickness = self.cleaned_data['thickness']
        raw_item = KesOrderRawItem.objects.get(id=self.cleaned_data['raw_item'].id)
        if thickness in {item.thickness for item in raw_item.produces.all()} and self.cleaned_data['product']:
            raise forms.ValidationError('该编号{}#已有相同的的厚度毛板存在！同一编号不允许有重复厚度的毛板行！'.format(raw_item.product))
        return thickness


class MoveLocationOrderForm(forms.ModelForm):
    class Meta:
        model = MoveLocationOrder
        exclude = ('order', 'location', 'location_dest', 'state')
        widgets = {
            'entry': forms.HiddenInput,
        }


class MoveLocationOrderItemForm(forms.ModelForm):
    class Meta:
        model = MoveLocationOrderItem
        fields = ('order', 'location', 'location_dest', 'product', 'piece', 'quantity', 'uom', 'package_list')
        widgets = {
            'order': forms.HiddenInput,
        }

    def __init__(self, *args, **kwargs):
        order = kwargs.pop('move_order')
        super(MoveLocationOrderItemForm, self).__init__(*args, **kwargs)
        if not kwargs.get('instance', None):
            loc = Location.objects.filter(id=order.location.id, is_virtual=False)
            dest = Location.objects.filter(id=order.location_dest.id, is_virtual=False)
            # onchange的ajax取数据url
            get_product_list = reverse_lazy('get_product_list')
            get_product_info = reverse_lazy('get_product_info')

            self.fields['location'].queryset = loc
            self.fields['location'].initial = order.location.id
            self.fields['location'].widget.attrs = {
                'onchange': 'onchange_set_product_list("{url}",{kwargs})'.format(url=get_product_list,
                                                                                 kwargs='{"location":this.value}')}
            self.fields['location_dest'].queryset = dest
            self.fields['location_dest'].initial = order.location_dest.id
            # 按初始化的仓库及本order已选择的product为条件筛选出product的qs
            order_products = [item.product.id for item in order.items.all()]
            loc_id = order.location.id
            loc_childs = Location.objects.get(pk=loc_id).child.all()
            loc_id = [loc_id]
            if loc_childs:
                loc_id.extend([c.id for c in loc_childs])
            qs = Product.objects.filter(stock__location_id__in=loc_id).exclude(id__in=order_products)
            self.fields['product'].queryset = qs
            self.fields['product'].widget.attrs = {
                'onchange': 'onchange_set_product_info({},"{}","quantity","piece", "uom")'.format('this.value',
                                                                                                  get_product_info)}
        # else:
        #     self.fields['product'].widget.attrs = {'disabled':True}


class SlabCheckInOrderForm(forms.ModelForm):
    class Meta:
        model = SlabCheckInOrder
        exclude = ('location', 'location_dest', 'state')
        widgets = {
            "order": forms.HiddenInput,
            "entry": forms.HiddenInput,

        }


class SlabCheckInOrderItemForm(forms.ModelForm):
    pass
