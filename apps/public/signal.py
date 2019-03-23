#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/12/6

# 更新该package list所对应的order item项数量
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import ForeignKey, OneToOneField, ManyToManyField, DateTimeField, DateField
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.forms import FileField

from mrp.models import ProductionOrderProduceItem, InOutOrderItem, TurnBackOrderItem, ProductionOrder, \
    MoveLocationOrder, MoveLocationOrderItem, InventoryOrderItem, InventoryOrderNewItem
from product.models import PackageList
from sales.models import SalesOrderItem
from comment.models import OperationLogs


def get_dict(obj):
    return {f.verbose_name: str(getattr(obj, f.name)) for f in obj._meta.fields if f.name != 'id'}


def to_dict(obj):
    obj_dict = get_dict(obj)
    items = obj.items.all()
    if items:
        for item in items:
            item_dict = get_dict(item)
            if hasattr(item, 'amount'):
                item_dict['金额'] = str(item.amount)
            if hasattr(item, 'produces'):
                for p in item.produces.all():
                    p_dict = get_dict(p)
                    if hasattr(p, 'amount'):
                        p_dict['金额'] = str(item.amount)
                    item_dict[p.line] = p_dict
            obj_dict[item.line] = item_dict
    return obj_dict


def compare(old_dict, new_dict):
    change = {}
    for key, value in old_dict.items():

        if isinstance(value, dict):
            if key in new_dict:
                old_dt, new_dt = old_dict[key], new_dict[key]
                change[key] = compare(old_dt, new_dt)
        elif key in new_dict:
            if value != new_dict[key]:
                change[key] = '%s=>%s' % (old_dict[key], new_dict[key])
        else:
            change[key] = '%s' % ("删除")
    for key, value in new_dict.items():
        if key not in old_dict:
            change[key] = '%s(%s)' % (new_dict[key], '添加')
    return change


# @receiver(pre_save, sender=MoveLocationOrder)
# @receiver(pre_save, sender=ProductionOrder)
# def pre_save_operation_logs(sender, **kwargs):
#     instance = kwargs.get('instance')
#     if instance.pk:
#         old_instance = instance.__class__.objects.get(pk=instance.pk)
#         old_dict = to_dict(old_instance)
#         new_dict = to_dict(instance)
#         change = compare(old_dict, new_dict)
#         instance.operation_logs.create(pre_data=change, from_order=instance)


@receiver(post_save, sender=PackageList, dispatch_uid='new_package')
def package_list_post_save_update_item_quantity(sender, **kwargs):
    instance = kwargs['instance']
    # 销售
    so_items = SalesOrderItem.objects.filter(package_list=instance)
    if so_items:
        for item in so_items:
            item.piece = instance.get_piece()
            item.quantity = instance.get_quantity()
            item.save()
        return True
    # 生产
    mo_produce_items = ProductionOrderProduceItem.objects.filter(package_list=instance)
    if mo_produce_items:
        for item in mo_produce_items:
            item.piece = instance.get_piece()
            item.quantity = instance.get_quantity()
            item.save()
        return True
    # 移库
    mv_items = MoveLocationOrderItem.objects.filter(package_list=instance)
    if mv_items:
        for item in mv_items:
            item.piece = instance.get_piece()
            item.quantity = instance.get_quantity()
            item.save()
        return True

    io_items = InOutOrderItem.objects.filter(package_list=instance)
    if io_items:
        for item in io_items:
            item.piece = instance.get_piece()
            item.quantity = instance.get_quantity()
            item.save()
        return True

    tb_items = TurnBackOrderItem.objects.filter(package_list=instance)
    if tb_items:
        tb_items[0].piece = instance.get_piece()
        tb_items[0].quantity = instance.get_quantity()
        tb_items[0].save()
        return True

    inv_items = InventoryOrderItem.objects.filter(now_package_list=instance)
    if inv_items:
        inv_items[0].now_piece = instance.get_piece()
        inv_items[0].now_quantity = instance.get_quantity()
        inv_items[0].save()
        return True

    inv_new_items = InventoryOrderNewItem.objects.filter(package_list=instance)
    if inv_new_items:
        for item in inv_new_items:
            item.piece = instance.get_piece()
            item.quantity = instance.get_quantity()
            item.save()
        return True
