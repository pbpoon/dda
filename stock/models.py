from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.urls import reverse
from django.contrib import messages

from product.models import Product, Slab

UOM_CHOICES = (('t', '吨'), ('m3', '立方'))

USAGE_CHOICES = (('supplier', '供应商库位'), ('customer', '客户库位'),
                 ('production', '生产库位'), ('internal', '存货库位'),
                 ('inventory', '盘点库位'))


class Warehouse(models.Model):
    """
    当创建一个warehouse时候，相应的创建一个内部的库位，为置顶库位
    """
    name = models.CharField('仓库名称', max_length=50, unique=True, db_index=True)
    code = models.CharField('缩写名称', max_length=20, null=False)
    is_activate = models.BooleanField('启用', default=True)
    partner = models.ForeignKey('partner.Partner', on_delete=models.SET_NULL, verbose_name='合作伙伴', null=True,
                                blank=True)
    created = models.DateTimeField('创建时间', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)
    is_production = models.BooleanField('有生产活动')

    class Meta:
        verbose_name = '仓库信息'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super(Warehouse, self).save(*args, **kwargs)
        if not self.locations.filter(is_main=True):
            Location.objects.create(warehouse_id=self.id, name='仓库', is_main=True)
        if self.is_production:
            Location.objects.get_or_create(warehouse_id=self.id, is_virtual=True, usage='production', name='生产库位')

    def get_absolute_url(self):
        return reverse('warehouse_detail', args=[self.id])

    def get_main_location(self):
        return self.locations.get(is_main=True, warehouse_id=self.id)


class Location(models.Model):
    """
    如果is_virtual=True,就不能有子库位
    """
    warehouse = models.ForeignKey('Warehouse', related_name='locations', on_delete=models.SET_NULL, verbose_name='所属仓库',
                                  blank=True, null=True)
    name = models.CharField('库位名称', max_length=50, unique=True)
    parent = models.ForeignKey('self', related_name='child', null=True, blank=True, verbose_name='上级库位',
                               on_delete=models.CASCADE, limit_choices_to={'is_virtual': False, 'is_activate': True})
    is_main = models.BooleanField('主库位', default=False, help_text='主库位，只有在创建warehouse时一并创建')
    usage = models.CharField('库位用途', choices=USAGE_CHOICES, null=False, max_length=50)
    is_virtual = models.BooleanField('虚拟库位', default=False)
    desc = models.TextField('描述', blank=True, null=True)
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
        return self.get_full_name()


class StockTrace(models.Model):
    """
    只在记录什么单的product操作了什么，用作链式记账
    """
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
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE, related_name='stock')
    piece = models.IntegerField('件', default=1)
    quantity = models.DecimalField('数量', decimal_places=2, max_digits=10)
    reserve_quantity = models.DecimalField('预留数量', decimal_places=2, max_digits=10, blank=True, null=True)
    reserve_piece = models.IntegerField('预留件', blank=True, null=True)
    uom = models.CharField('单位', choices=UOM_CHOICES, max_length=6)
    location = models.ForeignKey('Location', on_delete=models.CASCADE, limit_choices_to={'is_virtual': False},
                                 related_name='stock')
    created = models.DateTimeField('创建时间', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '库存'
        unique_together = ('product', 'location')
