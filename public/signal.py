#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/12/6

# 更新该package list所对应的order item项数量
from django.db.models.signals import post_save
from django.dispatch import receiver

from mrp.models import ProductionOrderProduceItem
from product.models import PackageList
from sales.models import SalesOrderItem


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
    mv_items = ProductionOrderProduceItem.objects.filter(package_list=instance)
    if mv_items:
        for item in mv_items:
            item.piece = instance.get_piece()
            item.quantity = instance.get_quantity()
            item.save()
        return True
