from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from product.models import Product

USAGE_CHOICES = (('supplier', '供应商库位'), ('customer', '客户库位'),
                 ('production', '生产库位'), ('internal', '存货库位'),
                 ('inventory', '盘点库位'))


class Warehouse(models.Model):
    name = models.CharField('仓库名称', max_length=50, null=False)
    code = models.CharField('缩写名称', max_length=20, null=False)
    is_activate = models.BooleanField('启用', default=True)
    partner = models.ForeignKey('partner.Partner', on_delete=models.SET_NULL, verbose_name='合作伙伴', null=True,
                                blank=True)
    created = models.DateTimeField('创建时间', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '仓库信息'

    def __str__(self):
        return self.name


class Location(models.Model):
    warehouse = models.ForeignKey('Warehouse', related_name='locations', on_delete=models.CASCADE, verbose_name='所属仓库')
    name = models.CharField('库位名称', max_length=50, null=False)
    parent = models.ForeignKey('self', related_name='child', null=True, blank=True, verbose_name='上级库位',
                               on_delete=models.CASCADE, )
    usage = models.CharField('库位用途', choices=USAGE_CHOICES, null=False, max_length=50)
    is_virtual = models.BooleanField('虚拟库位')
    desc = models.TextField('描述')
    is_activate = models.BooleanField('启用', default=True)
    created = models.DateTimeField('创建时间', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '库位信息'
        unique_together = ['warehouse', 'name']

    def get_full_name(self):
        name = self.name
        parent = self.parent
        while parent:
            name = '{}/{}'.format(parent.name, name)
            parent = parent.parent
        return name

    def __str__(self):
        return '{}/{}'.format(self.warehouse, self.name)


class StockTrace(models.Model):
    order_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='order_stock_trace')
    order_id = models.PositiveIntegerField()
    order = GenericForeignKey('order_content_type', 'order_id')
    location = models.ForeignKey('Location', related_name='stock_trace_from', verbose_name='库位',
                                 on_delete=models.DO_NOTHING)
    location_dest = models.ForeignKey('Location', related_name='stock_trace_to', verbose_name='目标库位',
                                      on_delete=models.DO_NOTHING)
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE, related_name='product_stock_trace')
    created = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '库存轨迹'

    def __str__(self):
        return '{}|{}:{}=>{}'.format(self.order, self.product, self.location, self.location_dest)


class Stock(models.Model):
    """只有location的is_virtual=True是才写入stock"""
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE, related_name='product_stock')
    pic
