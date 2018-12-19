#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/11/5
from django import forms
from django.urls import reverse, reverse_lazy

from mrp.models import ProductionOrder, ProductionOrderRawItem, ProductionOrderProduceItem, InOutOrder, InOutOrderItem, \
    Expenses, InventoryOrder, InventoryOrderItem, InventoryOrderNewItem
from mrp.models import TurnBackOrder, TurnBackOrderItem
from product.models import Product, PackageList
from public.forms import FormUniqueTogetherMixin
from public.widgets import AutocompleteWidget, OptionalChoiceField, CheckBoxWidget, RadioWidget
from stock.models import Location, Warehouse
from mrp.models import MoveLocationOrder, MoveLocationOrderItem


class MoveLocationOrderForm(forms.ModelForm):
    class Meta:
        model = MoveLocationOrder
        exclude = ('order', 'location', 'location_dest', 'state')
        widgets = {
            'entry': forms.HiddenInput,
        }


class MoveLocationOrderItemForm(FormUniqueTogetherMixin, forms.ModelForm):
    product_autocomplete = forms.CharField(label='产品编号', widget=AutocompleteWidget(url='get_product_list'))

    class Meta:
        model = MoveLocationOrderItem
        fields = ('order', 'location', 'location_dest', 'product_autocomplete', 'product', 'piece', 'quantity', 'uom',
                  'package_list')
        widgets = {
            'order': forms.HiddenInput,
            'product': forms.HiddenInput,
            'package_list': forms.HiddenInput,
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.uom = instance.product.get_uom()
        if not instance.package_list and instance.product.type == 'slab':
            instance.piece = 0
            instance.quantity = 0
        if commit:
            instance.save()
        return instance

    def __init__(self, *args, **kwargs):
        order = kwargs.pop('move_order')
        super(MoveLocationOrderItemForm, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance', None)
        if not instance:
            loc = Location.objects.filter(id=order.location.id, is_virtual=False)
            dest = Location.objects.filter(id=order.location_dest.id, is_virtual=False)
            # onchange的ajax取数据url
            get_product_list = reverse_lazy('get_product_list')
            get_product_info = reverse_lazy('get_product_info')

            self.fields['location'].queryset = loc
            self.fields['location'].initial = order.location.id
            # self.fields['location'].widget.attrs = {
            #     'onchange': 'onchange_set_product_list("{url}",{kwargs})'.format(url=get_product_list,
            #                                                                      kwargs='{"location":this.value}')}
            self.fields['location_dest'].queryset = dest
            self.fields['location_dest'].initial = order.location_dest.id
            # 按初始化的仓库及本order已选择的product为条件筛选出product的qs
            # order_products = [item.product.id for item in order.items.all()]
            # loc_id = order.location.id
            # loc_childs = Location.objects.get(pk=loc_id).child.all()
            # loc_id = [loc_id]
            # if loc_childs:
            #     loc_id.extend([c.id for c in loc_childs])
            # qs = Product.objects.filter(stock__location_id__in=loc_id).exclude(id__in=order_products)
            # self.fields['product'].queryset = qs
            # self.fields['product'].widget.attrs = {
            #     'onchange': 'onchange_set_product_info({},"{}","quantity","piece", "uom")'.format('this.value',
            #                                                                                       get_product_info)}

        else:
            self.fields['product_autocomplete'].initial = instance.product.name + instance.product.get_type_display()


class ProductionOrderForm(forms.ModelForm):
    class Meta:
        model = ProductionOrder
        fields = ('production_type', 'partner', 'warehouse', 'handler', 'date', 'entry')
        # exclude = ('order', 'location', 'location_dest', 'state')
        widgets = {
            'entry': forms.HiddenInput,
            # 'handler': forms.HiddenInput,
        }


class ProductionOrderRawItemForm(FormUniqueTogetherMixin, forms.ModelForm):
    product_autocomplete = forms.CharField(label='产品编号', widget=AutocompleteWidget(url='get_product_list'))
    type = forms.CharField(widget=forms.HiddenInput)

    class Meta:
        model = ProductionOrderRawItem
        fields = (
            'product_autocomplete', 'type', 'product', 'location', 'location_dest', 'order', 'line', 'piece',
            'quantity',
            'uom', 'price')
        widgets = {
            'location': forms.HiddenInput,
            'location_dest': forms.HiddenInput,
            'order': forms.HiddenInput,
            'line': forms.HiddenInput,
            'product': forms.HiddenInput,
        }

    def __init__(self, *args, **kwargs):
        order = kwargs.pop('production_order')
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        # 按order的原材料的type来筛选product的query_set
        this_product_id = None
        product_type = order.production_type.raw_item_type
        qs = Product.objects.filter(stock__location_id=order.location.id, type=product_type)
        self.fields['type'].initial = product_type
        if instance:
            # 如果是编辑状态，就把本荒料编号添加上
            self.fields['product_autocomplete'].initial = instance.product.name + instance.product.get_type_display()
            qs = qs.filter(id=kwargs.get('instance').product.id)
            this_product_id = qs[0].id
        elif order and order.items.all():
            # 如果是是新建状态，并且本order已经有原材料行，就把已经填写的原料的的产品剔出
            exclude_product_ids = [int(item.product.id) for item in order.items.all()]
            if this_product_id:
                exclude_product_ids = filter(lambda p: p != this_product_id, exclude_product_ids)
                qs.filter(type=product_type).exclude(pk__in=exclude_product_ids)
        # 把qs赋值到product的queryset
        # self.fields['product'].queryset = qs

        # onchange的ajax取数据url
        url = reverse_lazy('get_product_info')
        self.fields['product'].widget.attrs = {
            'onchange': 'onchange_set_product_info({},"{}","quantity")'.format('this', url)}

        # 根据product type的expense_by来设置price是否显示及是否必填
        if order.production_type.expense_by == 'produce':
            self.fields['price'].widget = forms.HiddenInput()
        else:
            self.fields['price'].required = True
        if product_type == 'block':
            self.fields['quantity'].required = True
        elif product_type == 'semi_slab':
            self.fields['piece'].widget.attrs = {'disabled': True}
            self.fields['piece'].label = '可用件数'
            # self.fields['piece'] = forms.HiddenInput()
            self.fields['quantity'].widget.attrs = {'disabled': True}
            self.fields['quantity'].label = '可用数量'
            # self.fields['quantity'] = forms.HiddenInput()
            # self.fields['uom'] = forms.HiddenInput()
            self.fields['uom'].initial = 'm2'


class ProductionOrderProduceItemForm(FormUniqueTogetherMixin, forms.ModelForm):
    # 以下2个是为了传值到quick create draft package list
    raw_product_name = forms.CharField(required=False, widget=forms.HiddenInput)
    raw_product_thickness = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = ProductionOrderProduceItem
        fields = ('order', 'raw_item', 'thickness', 'piece', 'quantity', 'price', 'package_list', 'draft_package_list',
                  'raw_product_name', 'raw_product_thickness')
        widgets = {
            'order': forms.HiddenInput,
            'raw_item': forms.HiddenInput,
            'draft_package_list': forms.HiddenInput,
            'package_list': forms.HiddenInput,
        }

    def __init__(self, *args, **kwargs):
        order = kwargs.pop('production_order')
        super().__init__(*args, **kwargs)
        product_type = order.production_type.produce_item_type
        # 根据生产的产品项来设置thickness的是否必填及是否显示
        if product_type == 'semi_slab':
            self.fields['thickness'].required = True
            self.fields['quantity'].widget = forms.HiddenInput()
        else:
            raw_product = ProductionOrderRawItem.objects.get(pk=kwargs['initial']['raw_item']).product
            self.fields['raw_product_name'].initial = str(raw_product)
            self.fields['raw_product_thickness'].initial = raw_product.thickness
            self.fields['thickness'].widget = forms.HiddenInput()
        # 根据product type的expense_by来设置price是否显示及是否必填
        if order.production_type.expense_by == 'raw':
            self.fields['price'].widget = forms.HiddenInput()
        else:
            self.fields['price'].required = True

    def clean_thickness(self):
        thickness = self.cleaned_data.get('thickness')
        if not thickness:
            return
        raw_item = self.cleaned_data['raw_item']
        if thickness in {item.thickness for item in raw_item.produces.all()} and self.cleaned_data.get('product'):
            raise forms.ValidationError('该编号{}#已有相同的的厚度毛板存在！同一编号不允许有重复厚度的毛板行！'.format(raw_item.product))
        return thickness


class InOutOrderForm(forms.ModelForm):
    class Meta:
        model = InOutOrder
        exclude = ('location', 'location_dest')
        widgets = {
            'entry': forms.HiddenInput,
            'purchase_order': forms.HiddenInput,
            'sales_order': forms.HiddenInput,
            'order': forms.HiddenInput,
            'state': forms.HiddenInput,
            'type': forms.HiddenInput,
            'partner': forms.HiddenInput,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        sales_order = kwargs['initial'].get('sales_order')
        if sales_order:
            self.fields['counter'].widget = forms.HiddenInput()
            qs = Warehouse.objects.filter(id__in=[item.location.warehouse.id for item in sales_order.items.all()])
            self.fields['warehouse'].queryset = qs
        else:
            self.fields['cart_number'].widget = forms.HiddenInput()
            self.fields['pickup_staff'].widget = forms.HiddenInput()


class InOutOrderItemForm(FormUniqueTogetherMixin, forms.ModelForm):
    class Meta:
        model = InOutOrderItem
        exclude = ('location', 'location_dest')
        widgets = {
            'order': forms.HiddenInput,
            'package_list': forms.HiddenInput,
        }


class MrpItemExpensesForm(forms.ModelForm):
    class Meta:
        model = Expenses
        fields = '__all__'
        widgets = {
            'content_type': forms.HiddenInput,
            'object_id': forms.HiddenInput,
        }


class TurnBackOrderForm(forms.ModelForm):
    class Meta:
        model = TurnBackOrder
        fields = ('content_type', 'object_id', 'reason', 'warehouse', 'entry', 'handler', 'date')
        widgets = {
            'entry': forms.HiddenInput,
            'content_type': forms.HiddenInput,
            'object_id': forms.HiddenInput,
        }


class TurnBackOrderItemForm(FormUniqueTogetherMixin, forms.ModelForm):
    class Meta:
        model = TurnBackOrderItem
        fields = '__all__'
        widgets = {
            'order': forms.HiddenInput,
            'package_list': forms.HiddenInput,
        }


class InventoryOrderForm(forms.ModelForm):
    class Meta:
        model = InventoryOrder
        fields = '__all__'
        widgets = {
            'state': forms.HiddenInput,
            'entry': forms.HiddenInput,
            'order': forms.HiddenInput,
        }


class InventoryOrderItemForm(FormUniqueTogetherMixin, forms.ModelForm):
    product_display = forms.CharField(widget=forms.TextInput(attrs={'disabled': True}), required=False, label='产品')

    class Meta:
        model = InventoryOrderItem
        fields = (
            'report', 'product_display', 'old_location', 'now_location', 'now_piece', 'now_quantity', 'uom', 'ps',
            'product',
            'entry', 'order', 'line', 'now_package_list', 'old_quantity', 'old_piece',)
        widgets = {
            'product': forms.HiddenInput,
            'entry': forms.HiddenInput,
            'order': forms.HiddenInput,
            'line': forms.HiddenInput,
            'location': forms.HiddenInput,
            'old_piece': forms.HiddenInput,
            'old_quantity': forms.HiddenInput,
            'ps': forms.Textarea,
            'report': RadioWidget(attrs={'class': 'with-gap'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        qs = Location.objects.filter(id__in=instance.order.warehouse.get_main_location().get_child_list()).distinct()
        self.fields['now_location'].queryset = qs
        self.fields['now_location'].initial = instance.old_location.id
        self.fields['product_display'].initial = instance.product
        self.fields['now_piece'].widget.attrs = {'placeholder': instance.old_piece}
        self.fields['now_quantity'].widget = forms.TextInput(
            attrs={'placeholder': instance.old_quantity, 'class': "validate"})

    def clean(self):
        cd = self.cleaned_data
        report = cd.get('report')
        now_piece = cd.get('now_piece')
        now_quantity = cd.get('now_quantity')
        if report == 'not_equal':
            if not now_piece or not now_quantity:
                raise forms.ValidationError('盘点件及数量不能为空')
        return cd


class InventoryOrderNewItemForm(forms.ModelForm):
    name_autocomplete = forms.CharField(label='产品编号',
                                        widget=AutocompleteWidget(url='get_block_list', onAutocomplete_function='set_block'))

    class Meta:
        model = InventoryOrderNewItem
        fields = (
            'product_type', 'name_autocomplete', 'block', 'thickness', 'location_dest', 'piece', 'quantity', 'uom',
            'ps', 'product', 'entry',
            'order',
            'line', 'package_list', 'draft_package_list', 'location')

        widgets = {
            'block': forms.HiddenInput,
            'order': forms.HiddenInput,
            'entry': forms.HiddenInput,
            'line': forms.HiddenInput,
            'location': forms.HiddenInput,
            'product': forms.HiddenInput,
            'package_list': forms.HiddenInput,
            'draft_package_list': forms.HiddenInput,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        order = kwargs['initial'].get('order')
        instance = kwargs.get('instance')
        qs = Location.objects.filter(id__in=order.warehouse.get_main_location().get_child_list()).distinct()
        self.fields['location_dest'].queryset = qs
        self.fields['location'].initial = Location.get_inventory_location().id
        if order.product_type:
            self.fields['product_type'].initial = order.product_type
            self.fields['product_type'].widget.attrs = {'disabled': True}
            self.fields['product_type'].required = False
            if order.product_type != 'block':
                self.fields['uom'].initial = 'm2'
        else:
            self.fields['product_type'].required = True
        if instance:
            self.fields['name_autocomplete'].initial = instance.product


    def clean_block(self):
        block = self.cleaned_data.get('block')
        if not block:
            raise forms.ValidationError('请输入正确的编号')
        return block

    def clean(self):
        cd = self.cleaned_data
        product_type = cd.get('product_type')
        order = cd.get('order')
        if not order.product_type and not product_type:
            raise forms.ValidationError('请输入产品类型')
        if not product_type and order.product_type:
            cd['product_type'] = order.product_type
        if order.product_type == 'block':
            cd['piece'] = 1
        else:
            cd['uom'] = 'm2'
        cd['product'] = cd['block'].create_product(type=cd['product_type'], defaults={'name': cd['block'].name},
                                                   thickness=cd.get('thickness'))
        if cd['product_type'] == 'slab':
            cd['package_list'] = PackageList.objects.create(product=cd['product'])
        return cd
