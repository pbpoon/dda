import math
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import decimal
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

from public.fields import OrderField
from purchase.models import OrderAbstract

UOM_CHOICES = (('t', '吨'), ('m3', '立方'), ('m2', '平方'))


class MrpOrderAbstract(OrderAbstract):
    location = models.ForeignKey('stock.Location', on_delete=models.SET_NULL, related_name='%(class)s_location',
                                 verbose_name='原库位', null=True, blank=True)
    location_dest = models.ForeignKey('stock.Location', on_delete=models.SET_NULL,
                                      related_name='%(class)s_location_dest',
                                      verbose_name='目标库位', null=True, blank=True)
    stock_trace = GenericRelation('stock.StockTrace')
    warehouse = models.ForeignKey('stock.Warehouse', on_delete=models.CASCADE, verbose_name='仓库')

    class Meta:
        abstract = True

    def get_location(self):
        raise ValueError('没有设置get_location')

    def get_location_dest(self):
        raise ValueError('没有设置get_location_dest')

    def save(self, *args, **kwargs):
        self.location = self.get_location()
        self.location_dest = self.get_location_dest()
        super(MrpOrderAbstract, self).save(*args, **kwargs)

    def __str__(self):
        return self.order


class OrderItemBase(models.Model):
    location = models.ForeignKey('stock.Location', related_name='%(class)s_location', verbose_name='库位',
                                 on_delete=models.DO_NOTHING, blank=True, null=True)
    location_dest = models.ForeignKey('stock.Location', related_name='%(class)s_location_dest', verbose_name='目标库位',
                                      on_delete=models.DO_NOTHING, blank=True, null=True)
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE, verbose_name='product')
    piece = models.IntegerField('件', default=1)
    quantity = models.DecimalField('数量', decimal_places=2, max_digits=10)
    uom = models.CharField('计量单位', null=False, choices=UOM_CHOICES, max_length=10, default='t')

    class Meta:
        abstract = True

    def get_location(self):
        return self.order.location

    def get_location_dest(self):
        return self.order.location_dest

    def save(self, *args, **kwargs):
        self.location = self.get_location()
        self.location_dest = self.get_location_dest()
        super(OrderItemBase, self).save(*args, **kwargs)

