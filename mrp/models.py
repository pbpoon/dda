from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

from purchase.fields import OrderField
from purchase.models import OrderAbstract

UOM_CHOICES = (('t', '吨'), ('m3', '立方'))


class MrpOrderAbstract(OrderAbstract):
    location = models.ForeignKey('stock.Location', on_delete=models.SET_NULL, related_name='%(class)s_location_from',
                                 verbose_name='原库位', null=True, blank=True)
    location_dest = models.ForeignKey('stock.Location', on_delete=models.SET_NULL, related_name='%(class)s_location_to',
                                      verbose_name='目标库位', null=True, blank=True)
    stock_trace = GenericRelation('stock.StockTrace')

    class Meta:
        abstract = True


class OrderItemBase(models.Model):
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE, verbose_name='product')
    piece = models.IntegerField('件', default=1)
    quantity = models.DecimalField('数量', decimal_places=2, max_digits=10)
    uom = models.CharField('计量单位', null=False, choices=UOM_CHOICES, max_length=10, default='t')

    class Meta:
        abstract = True


class BlockCheckInOrder(MrpOrderAbstract):
    order = OrderField(order_str='BI', blank=True, verbose_name='单号', default='New', max_length=20)
    counter = models.IntegerField('货柜数', blank=True, null=True)
    purchase_order = models.ForeignKey('purchase.PurchaseOrder', on_delete=models.CASCADE, verbose_name='采购订单',
                                       related_name='block_check_in_order')
    warehouse = models.ForeignKey('stock.Warehouse', on_delete=models.CASCADE, verbose_name='卸货仓库')

    class Meta:
        verbose_name = '荒料到货入库单'

    def get_absolute_url(self):
        return reverse('block_check_in_detail', args=[self.id])


class BlockCheckInOrderItem(OrderItemBase):
    order = models.ForeignKey('BlockCheckInOrder', on_delete=models.CASCADE, related_name='items', blank=True,
                              null=True)

    class Meta:
        verbose_name = '荒料到货入库单明细项'


class KesOrder(MrpOrderAbstract):
    order = OrderField(order_str='KS', blank=True, verbose_name='单号', default='New', max_length=20)

    class Meta:
        verbose_name = '界石加工单'


class KesOrderRawItem(OrderItemBase):
    order = models.ForeignKey('KesOrder', on_delete=models.CASCADE, related_name='items', blank=True,
                              null=True)
    price = models.DecimalField('单价', max_digits=8, decimal_places=2)

    class Meta:
        verbose_name = '界石单荒料项'

    def get_amount(self):
        return self.quantity * self.price


class KesOrderProduceItem(OrderItemBase):
    order = models.ForeignKey('KesOrder', on_delete=models.CASCADE, related_name='produce_items', blank=True, null=True,
                              verbose_name='对应界石单')
    raw_item = models.ForeignKey('KesOrderRawItem', on_delete=models.CASCADE, related_name='produces',
                                 verbose_name='原材料')
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE, verbose_name='product', blank=True,
                                null=True)
    thickness = models.DecimalField('厚度规格', max_digits=5, decimal_places=2, null=True, blank=True)
    quantity = models.DecimalField('数量', decimal_places=2, max_digits=10, null=True, blank=True)

    class Meta:
        verbose_name = '界石单毛板项'

    def estimate_quantity(self):
        """写好库存选料后再回来写"""
        pass