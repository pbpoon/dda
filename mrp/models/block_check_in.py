
from django.db import models
from django.urls import reverse

from mrp.models import MrpOrderAbstract, OrderItemBase
from public.fields import OrderField

UOM_CHOICES = (('t', '吨'), ('m3', '立方'), ('m2', '平方'))


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

    def get_item_edit_url(self):
        return reverse('block_check_in_item_edit')

    def get_location(self):
        return self.purchase_order.partner.get_location()

    def get_location_dest(self):
        return self.warehouse.get_main_location()

    def get_update_url(self):
        return None


class BlockCheckInOrderItem(OrderItemBase):
    order = models.ForeignKey('BlockCheckInOrder', on_delete=models.CASCADE, related_name='items', blank=True,
                              null=True)

    class Meta:
        verbose_name = '荒料到货入库单明细行'

