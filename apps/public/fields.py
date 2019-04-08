#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by pbpoon on 2018/10/27
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

class LineField(models.PositiveIntegerField):
    def __init__(self, for_fields=None, *args, **kwargs):
        # 初始化参数比父类多一个for_fields字段
        self.for_fields = for_fields
        # 调用父类初始化方法进行其他参数的初始化
        super().__init__(*args, **kwargs)

    # 重写 pre_save()方法
    def pre_save(self, model_instance, add):
        # 通过反射取自己的值，attname对应的是自己的内置.name属性也就是字段名
        if getattr(model_instance, self.attname) is None:
            # 如果没有值，查询自己所在表的全部内容，找到最后一条字段，设置临时变量value = 最后字段的序号+1
            try:
                # 取自己所在数据表内全部对象（行）
                qs = self.model.objects.all()
                # 判断是否传入for_fields参数
                if self.for_fields:
                    # 存在for_fields参数，通过该参数取对应的数据行
                    query = {field: getattr(model_instance, field) for field in self.for_fields}
                    qs = qs.filter(**query)
                last_item = qs.latest(self.attname)
                value = getattr(last_item, self.attname) + 1
            # 如果找不到最后一条数据，说明自己是第一条数据，将临时变量value 设置为0
            except ObjectDoesNotExist:
                value = 1
            # 将 value 变量存入自己内部
            setattr(model_instance, self.attname, value)
            return value
        else:
            # 如果有值，不做任何处理，直接调用父类的pre_save()方法
            return super().pre_save(model_instance, add)


class OrderField(models.CharField):
    def __init__(self, order_str=None, *args, **kwargs):

        self.order_str = order_str
        super(OrderField, self).__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        attname_value = getattr(model_instance, self.attname)
        if attname_value == 'New' or not attname_value:
            #如果是新记录
            date_str = timezone.now().strftime('%y%m')
            # 转换时间格式为str
            value = self.order_str + date_str + '001'
            # 把value初始化成 order_str + 年月 + 001
            try:
                # 取自己所在数据表内全部对象（行）
                qs = self.model.objects.all()
                # 判断是否传入for_fields参数
                # 格式为 IM1703001
                last_order = qs.latest(self.attname)
                last_order_str = getattr(last_order, self.attname)
                if date_str in last_order_str[2:6]:
                    value = self.order_str + str(int(last_order_str[2:9]) + 1)
            except ObjectDoesNotExist:
                pass
            setattr(model_instance, self.attname, value)
            return value
        else:
            return super(OrderField, self).pre_save(model_instance, add)
