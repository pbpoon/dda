from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation, ContentType
from django.db import models
from django.urls import reverse
from datetime import datetime

from mrp.models import MrpOrderAbstract, OrderItemBase
from public.fields import OrderField, LineField

TYPE_CHOICES = (('block', '荒料'), ('semi_slab', '毛板'), ('slab', '板材'))
UOM_CHOICES = (('t', '吨'), ('m3', '立方'), ('m2', '平方'))
OPERATION_TYPE = (('in', '入库'), ('out', '出库'))
STATE_CHOICES = (
    ('draft', '草稿'),
    ('confirm', '确认'),
    ('done', '完成'),
    ('cancel', '取消'),
)


class InventoryOrder(models.Model):
    name = models.CharField('盘点简述', max_length=100)
    state = models.CharField('状态', choices=STATE_CHOICES, max_length=20, default='draft')

    order = OrderField(order_str='INV', blank=True, verbose_name='单号', default='New', max_length=20)
    warehouse = models.ForeignKey('stock.Warehouse', on_delete=models.CASCADE, verbose_name='仓库', blank=True,
                                  null=True, help_text='盘点的仓库')
    product_type = models.CharField('产品类型', max_length=10, choices=TYPE_CHOICES, blank=True, null=True)
    handler = models.ManyToManyField('auth.User', verbose_name='经办人',
                                     related_name='%(class)s_handler')
    entry = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name='登记人',
                              related_name='%(class)s_entry')
    date = models.DateField('日期', default=datetime.now)
    created = models.DateField('创建日期', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '盘点库存'

    def get_absolute_url(self):
        return reverse('inventory_order_detail', args=[self.id])

    def get_create_item_url(self):
        return reverse('inventory_order_item_create', args=[self.id])

    def __str__(self):
        return self.name


class InventoryOrderItem(models.Model):
    order = models.ForeignKey('InventoryOrder', on_delete=models.CASCADE, related_name='items', verbose_name='对应订单')
    line = LineField(for_fields=['order'], blank=True, verbose_name='行')
    is_equal = models.BooleanField('与原数据相符', default=False)
    is_done = models.BooleanField('完成', default=False)
    is_lose = models.BooleanField('丢失', default=False, help_text='已不在库的')
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE, verbose_name='产品')
    old_location = models.ForeignKey('stock.Location', related_name='%(class)s_old_location', verbose_name='原库位',
                                     on_delete=models.DO_NOTHING, blank=True, null=True)
    location = models.ForeignKey('stock.Location', related_name='%(class)s_location', verbose_name='实际库位',
                                 on_delete=models.DO_NOTHING, blank=True, null=True, limit_choices_to={'is_virtual':False})
    old_piece = models.IntegerField('原件数', default=1)
    old_quantity = models.DecimalField('原数量', decimal_places=2, max_digits=10)
    piece = models.IntegerField('实际件数', blank=True, null=True)
    quantity = models.DecimalField('实际数量', decimal_places=2, max_digits=10, blank=True, null=True)
    uom = models.CharField('计量单位', null=False, choices=UOM_CHOICES, max_length=10, default='t')
    old_package_list = models.ForeignKey('product.PackageList', on_delete=models.SET_NULL, blank=True, null=True,
                                         verbose_name='码单', related_name='%(class)s_old_package_list')
    package_list = models.ForeignKey('product.PackageList', on_delete=models.SET_NULL, blank=True, null=True,
                                     verbose_name='码单')
    draft_package_list = models.ForeignKey('product.DraftPackageList', on_delete=models.SET_NULL, blank=True, null=True,
                                           verbose_name='草稿码单')
    ps = models.CharField('备注', max_length=120, blank=True, null=True)
    entry = models.ForeignKey('auth.User', on_delete=models.SET_NULL, verbose_name='登记人',
                              related_name='%(class)s_entry', blank=True, null=True)

    class Meta:
        verbose_name = '盘点库存明细行'

    def save(self, *args, **kwargs):
        if self.package_list:
            self.piece = self.package_list.get_piece()
            self.quantity = self.package_list.get_quantity()
        super().save(*args, **kwargs)
