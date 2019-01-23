#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/11/5
from django import forms
from django.urls import reverse, reverse_lazy

from mrp.models import ProductionOrder, ProductionOrderRawItem, ProductionOrderProduceItem, InOutOrder, InOutOrderItem, \
    Expenses, InventoryOrder, InventoryOrderItem, InventoryOrderNewItem, MrpSupplier
from mrp.models import TurnBackOrder, TurnBackOrderItem
from product.models import Product, PackageList
from public.forms import FormUniqueTogetherMixin
from public.widgets import AutocompleteWidget, OptionalChoiceField, SwitchesWidget, RadioWidget
from stock.models import Location, Warehouse
from mrp.models import MoveLocationOrder, MoveLocationOrderItem
from dal import autocomplete


class MoveLocationOrderForm(forms.ModelForm):
    class Meta:
        model = MoveLocationOrder
        exclude = ('order', 'location', 'location_dest', 'state')
        widgets = {
            'entry': forms.HiddenInput,
        }
    #
    # def clean(self):
    #     cd = self.cleaned_data
    #     if cd['warehouse'] == cd['warehouse_dest']:
    #         raise forms.ValidationError('移出仓库 与 目标仓库 不能相同')
    #     return cd


class MoveLocationOrderItemForm(FormUniqueTogetherMixin, forms.ModelForm):
    # product_autocomplete = forms.CharField(label='产品编号', widget=AutocompleteWidget(url='get_product_list'))

    class Meta:
        model = MoveLocationOrderItem
        fields = ('order', 'location', 'location_dest', 'product', 'piece', 'quantity', 'uom',
                  'package_list')
        widgets = {
            'order': forms.HiddenInput,
            'package_list': forms.HiddenInput,
            'product': autocomplete.ModelSelect2(url='get_product_list',
                                                 attrs={'class': 'browser-default'},
                                                 forward=['location']),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.uom = instance.product.get_uom()
        if not instance.package_list and instance.product.type == 'slab':
            instance.piece = 0
            instance.quantity = 0
        elif instance.product.type == 'semi_slab':
            instance.quantity = instance.product.semi_slab_single_qty * instance.piece
        if commit:
            instance.save()
        return instance

    def __init__(self, *args, **kwargs):
        order = kwargs.pop('move_order')
        super(MoveLocationOrderItemForm, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance', None)
        if not instance:
            loc = Location.objects.filter(id__in=Location.objects.get(id=order.location.id).get_child_list())
            # loc = Location.objects.filter(id=order.location.id, is_virtual=False)
            dest = Location.objects.filter(id__in=Location.objects.get(id=order.location_dest.id).get_child_list())
            # onchange的ajax取数据url

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
    type = forms.CharField(widget=forms.HiddenInput)
    m3 = forms.DecimalField(label='立方', required=False)

    class Meta:
        model = ProductionOrderRawItem
        fields = (
            'type', 'product', 'location', 'location_dest', 'order', 'line', 'piece',
            'quantity',
            'uom', 'm3', 'price')
        widgets = {
            'location': forms.HiddenInput,
            'location_dest': forms.HiddenInput,
            'order': forms.HiddenInput,
            'line': forms.HiddenInput,
            'product': autocomplete.ModelSelect2(url='get_product_list',
                                                 attrs={'class': 'browser-default'},
                                                 forward=['location', 'type']),
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
        # url = reverse_lazy('get_product_info')
        # self.fields['product'].widget.attrs = {
        #     'onchange': 'onchange_set_product_info({},"{}","quantity")'.format('this', url)}

        # 根据product type的expense_by来设置price是否显示及是否必填
        if order.production_type.expense_by == 'produce':
            self.fields['price'].widget = forms.HiddenInput()
        else:
            self.fields['price'].required = True
        if product_type == 'block':
            self.fields['quantity'].required = True
        if product_type != 'block':
            self.fields['m3'].widget = forms.HiddenInput()
        elif product_type == 'semi_slab':
            self.fields['piece'].widget.attrs = {'disabled': True}
            self.fields['piece'].label = '可用件数'
            # self.fields['piece'] = forms.HiddenInput()
            self.fields['quantity'].widget.attrs = {'disabled': True}
            self.fields['quantity'].label = '可用数量'
            # self.fields['quantity'] = forms.HiddenInput()
            # self.fields['uom'] = forms.HiddenInput()
            self.fields['uom'].initial = 'm2'

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.product.type == 'block':
            m3 = self.cleaned_data.get('m3')
            instance.piece = 1
            instance.quantity = m3
            instance.uom = 'm3'
        if commit:
            instance.save()
        return instance


class ProductionOrderProduceItemForm(FormUniqueTogetherMixin, forms.ModelForm):
    # 以下2个是为了传值到quick create draft package list
    # raw_product_name = forms.CharField(required=False, widget=forms.HiddenInput)
    # raw_product_thickness = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = ProductionOrderProduceItem
        fields = ('order', 'raw_item', 'thickness', 'piece', 'pic', 'pi', 'quantity', 'price', 'package_list',
                  'draft_package_list')
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
            self.fields['piece'].widget = forms.HiddenInput()
            self.fields['pic'].widget = forms.NumberInput()
            self.fields['pi'].widget = forms.NumberInput()
            self.fields['pic'].required = True
            self.fields['pi'].required = True
            self.fields['piece'].widget = forms.HiddenInput()
            self.fields['quantity'].widget = forms.HiddenInput()
        else:
            raw_product = ProductionOrderRawItem.objects.get(pk=kwargs['initial']['raw_item']).product
            # self.fields['raw_product_name'].initial = str(raw_product)
            # self.fields['raw_product_thickness'].initial = raw_product.thickness
            self.fields['thickness'].widget = forms.HiddenInput()
            self.fields['thickness'].initial = raw_product.thickness
            self.fields['piece'].widget = forms.HiddenInput()
            self.fields['quantity'].widget = forms.HiddenInput()

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

    def save(self, commit=True):
        cd = self.cleaned_data
        instance = super().save(commit=False)
        # cd['order'] = self.raw_item.order
        # thickness = self.thickness or self.raw_item.product.thickness
        if not instance.product:
            instance.product = instance.raw_item.product.create_product(
                type=cd['order'].production_type.produce_item_type,
                thickness=cd['thickness'])
            if instance.product.type == 'slab':
                instance.package_list = PackageList.objects.create(product=instance.product,
                                                                   return_path=instance.order.get_absolute_url())
        if instance.product.type == 'semi_slab':
            instance.piece = instance.pic + instance.pi
        if instance.package_list:
            instance.quantity = instance.package_list.get_quantity()
            instance.piece = instance.package_list.get_piece()
        instance.uom = instance.product.get_uom()
        if commit:
            instance.save()
        return instance


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

    def clean_quantity(self):
        cd = self.cleaned_data
        expense_by_uom = cd.get('expense_by_uom')
        if expense_by_uom == 'another' and not cd.get('quantity', None):
            raise forms.ValidationError('必须输入数量')
        return cd['quantity']


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
    old_location_display = forms.CharField(widget=forms.TextInput(attrs={'disabled': True}), required=False, label='原库位')

    class Meta:
        model = InventoryOrderItem
        fields = (
            'report', 'product_display', 'old_location', 'old_location_display','now_location', 'now_piece', 'now_quantity', 'uom', 'ps',
            'product',
            'entry', 'order', 'line', 'now_package_list', 'old_package_list', 'old_quantity', 'old_piece',
            'package_list', 'piece',
            'quantity')
        widgets = {
            'product': forms.HiddenInput,
            'entry': forms.HiddenInput,
            'order': forms.HiddenInput,
            'line': forms.HiddenInput,
            'location': forms.HiddenInput,
            'old_location': forms.HiddenInput,
            'old_piece': forms.HiddenInput,
            'piece': forms.HiddenInput,
            'quantity': forms.HiddenInput,
            'old_quantity': forms.HiddenInput,
            'old_package_list': forms.HiddenInput,
            'now_package_list': forms.HiddenInput,
            'package_list': forms.HiddenInput,
            'ps': forms.Textarea,
            'report': RadioWidget(attrs={'class': 'with-gap'}),
            'now_location': autocomplete.ModelSelect2(url='location_autocomplete',
                                                      attrs={'class': 'browser-default'},
                                                      forward=['old_location'])
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        # qs = Location.objects.filter(id__in=instance.order.warehouse.get_main_location().get_child_list()).distinct()
        # self.fields['now_location'].queryset = qs
        # self.fields['now_location'].initial = instance.old_location.id
        self.fields['product_display'].initial = instance.product
        self.fields['old_location_display'].initial = instance.old_location
        self.fields['now_piece'].widget.attrs = {'placeholder': instance.old_piece}
        self.fields['now_quantity'].widget = forms.TextInput(
            attrs={'placeholder': instance.old_quantity, 'class': "validate"})
        if instance.product.type == 'slab':
            self.fields['now_piece'].widget = forms.HiddenInput()
            self.fields['now_quantity'].widget = forms.HiddenInput()

    def get_diff_piece(self):
        cd = self.cleaned_data
        n_p = cd.get('now_piece', 0)
        piece = abs(n_p - cd.get('old_piece'))
        return piece

    def get_diff_quantity(self):
        cd = self.cleaned_data
        n_q = cd.get('now_quantity', 0)
        quantity = abs(n_q - cd['old_quantity'])
        return quantity

    def get_diff_slab_ids(self):
        cd = self.cleaned_data
        if cd['product'].type == 'slab':
            old_slab_ids = cd['old_package_list'].items.values_list('slab', flat=True)
            now_slab_ids = cd['now_package_list'].items.values_list('slab', flat=True)
            diff_slab_ids = set(old_slab_ids) ^ set(now_slab_ids)
            return diff_slab_ids
        return None

    # 如果选择是未盘点
    def set_None(self):
        cd = self.cleaned_data
        cd['now_piece'], cd['piece'] = None, None
        cd['now_quantity'], cd['quantity'] = None, None
        return cd

    # 如果盘点为相等，就把现在的数量等于之前的数量
    # 并且如果盘点的是毛板，有码单的，就把盘点的数量
    def set_is_equal(self):
        cd = self.cleaned_data
        cd['now_piece'] = cd['old_piece']
        cd['now_quantity'] = cd['old_quantity']
        cd['piece'] = cd['old_piece']
        cd['quantity'] = cd['old_quantity']
        cd['location'] = cd['old_location']
        cd['location_dest'] = cd['now_location']
        if cd.get('old_package_list'):
            slab_ids_list = [item.get_slab_id() for item in cd['old_package_list'].items.all()]
            cd['package_list'].update(cd['package_list'], slab_ids_list)
            cd['now_package_list'].update(cd['now_package_list'], slab_ids_list)
        cd['location'], cd['location_dest'] = cd['old_location'], cd['now_location']
        return cd
        # 如果盘点选项是 is_lose就把now的数据设置为0，把实际的数据设置为old的数据

    def set_is_lose(self):
        cd = self.cleaned_data
        cd['now_piece'] = 0
        cd['now_quantity'] = 0
        cd['piece'] = cd['old_piece']
        cd['quantity'] = cd['old_quantity']
        cd['location'] = cd['old_location']
        cd['location_dest'] = cd['old_location'].get_inventory_location()
        if cd.get('old_package_list'):
            slab_ids_list = [item.get_slab_id() for item in cd['old_package_list'].items.all()]
            if slab_ids_list:
                cd['now_package_list'].update(cd['now_package_list'], slab_ids_list)
        cd['location'], cd['location_dest'] = cd['old_location'], cd['old_location'].get_inventory_location()
        return cd

    def set_not_equal(self):
        cd = self.cleaned_data
        if cd['now_piece'] == 0:
            cd['report'] = 'is_lose'
            return self.set_is_lose()
        elif cd['now_piece'] == cd['old_piece']:
            if cd['product'].type != 'slab':
                cd['report'] = 'is_equal'
                return self.set_is_equal()
        n_p = cd.get('now_piece', 0)
        n_q = cd.get('now_quantity', 0)
        if cd['now_package_list']:
            cd['now_quantity'] = cd['now_package_list'].get_quantity()
            cd['now_piece'] = cd['now_package_list'].get_piece()
        cd['piece'] = 0 if cd['product'].type == 'block' else self.get_diff_piece()
        cd['quantity'] = self.get_diff_quantity()
        if cd['old_package_list']:
            PackageList.update(cd['package_list'], self.get_diff_slab_ids())

        if (n_p - cd['old_piece']) > 0 or (n_q - cd['old_quantity']) > 0:
            cd['location'], cd['location_dest'] = cd['old_location'].get_inventory_location(), cd['now_location']
        else:
            cd['location'], cd['location_dest'] = cd['old_location'].get_inventory_location(), cd['now_location']

    def clean_report(self):
        report = self.cleaned_data.get('report')
        if report == None:
            raise forms.ValidationError('请选择盘点情况')
        return report

    def clean(self):
        cd = self.cleaned_data
        report = cd.get('report')
        now_piece = cd.get('now_piece')
        now_quantity = cd.get('now_quantity')
        if report == 'not_equal':
            if not now_piece or not now_quantity:
                raise forms.ValidationError('盘点件及数量不能为空')
        if report == None:
            cd = self.set_None()
        else:
            attr = 'set_%s' % (report)
            cd = getattr(self, attr)()
        return cd


class InventoryOrderNewItemForm(forms.ModelForm):
    # name_autocomplete = forms.CharField(label='产品编号',
    #                                     widget=AutocompleteWidget(url='get_block_list',
    #                                                               onAutocomplete_function='set_block'))

    class Meta:
        model = InventoryOrderNewItem
        fields = (
            'product_type',  'block', 'thickness', 'location_dest', 'piece', 'quantity', 'uom',
            'ps', 'product', 'entry',
            'order',
            'line', 'package_list', 'draft_package_list', 'location')

        widgets = {
            'block': autocomplete.ModelSelect2(url='block_autocomplete', attrs={'class': 'browser-default'}),
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
            if order.product_type == 'block':
                self.fields['thickness'].widget = forms.HiddenInput()
                self.fields['piece'].initial = '1'
                self.fields['piece'].widget = forms.HiddenInput()
            else:
                self.fields['uom'].initial = 'm2'
        else:
            self.fields['product_type'].required = True
        # if instance:
        #     self.fields['name_autocomplete'].initial = instance.product

    def clean_block(self):
        block = self.cleaned_data.get('block')
        if not block:
            raise forms.ValidationError('请输入正确的编号')
        return block

    def clean(self):
        from product.models import Block
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
        cd['product'] = Block.create_product(type=cd['product_type'], defaults={}, name=cd['block'].name,
                                             thickness=cd.get('thickness', None))
        if cd['product_type'] == 'slab':
            cd['package_list'] = PackageList.objects.create(product=cd['product'])
        return cd


class SupplierForm(forms.ModelForm):
    type = forms.TypedChoiceField(label='伙伴类型', choices=(('production', '生产单位'), ('service', '运输/服务商')),
                                  widget=RadioWidget)

    class Meta:
        model = MrpSupplier
        fields = (
            'is_company', 'type', 'sex', 'name', 'phone', 'province', 'city', 'entry')
        widgets = {
            'sex': RadioWidget(),
            'type': RadioWidget(),
            'is_company': SwitchesWidget,
            'is_activate': SwitchesWidget,
            'entry': forms.HiddenInput(),
            'province': autocomplete.ModelSelect2(url='get_province',
                                                  attrs={'class': 'browser-default'}),
            'city': autocomplete.ModelSelect2(url='get_city',
                                              forward=['province'],
                                              attrs={'class': ' browser-default'})
        }
