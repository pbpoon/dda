import math
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import decimal
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

    def get_absolute_url(self):
        return reverse('kes_order_detail', args=[self.id])

    def get_item_edit_url(self):
        return reverse('kes_order_raw_item_edit')


class KesOrderRawItem(OrderItemBase):
    order = models.ForeignKey('KesOrder', on_delete=models.CASCADE, related_name='items', blank=True,
                              null=True)
    price = models.DecimalField('单价', max_digits=8, decimal_places=2, help_text='立方单价')
    m3 = models.DecimalField('立方数', max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = '界石单荒料项'

    def get_amount(self):
        m3 = self.m3 if self.m3 else 0
        return m3 * self.price

    def __str__(self):
        return str(self.product)

    def save(self, *args, **kwargs):
        if not self.m3:
            self.m3 = self.product.get_m3()
        super(KesOrderRawItem, self).save(*args, **kwargs)

    def single_qty(self):
        # 先取出对应的item的最小的厚度
        all_produces = self.produces.all()
        all_produces_dict = {i.thickness: i.piece for i in all_produces}
        min_thickness = min_thickness_key = min(all_produces_dict.keys())
        # 把最小如果是1。5的就改成1。4，之后把厚度+0。43刀头的厚度
        min_thickness = decimal.Decimal(1.4) if min_thickness == 1.5 else min_thickness
        min_thickness += decimal.Decimal(0.43)
        # 用m3 x 厚度出材率计算出最小规格的总出材率
        m3 = self.product.get_m3()
        total_min_thickness_m2 = m3 * (decimal.Decimal(100) - min_thickness) / min_thickness
        total_min_piece = all_produces_dict[min_thickness_key]
        # 如果该荒料的规格厚度为多个，就用其他厚度x件数就算出该厚度为最小厚度的件数，
        # 用最小厚度添加计算出来的件数，最总计算出如果该料界最小厚度会有多少件数，最后用最小厚度的总估算平方数除以估算的总件，计算出单价平方数
        if len(all_produces) > 1:
            for i in all_produces:
                total_min_piece += math.ceil((i.thickness + decimal.Decimal(0.43) * i.piece / min_thickness))
        single_qty = total_min_thickness_m2 / total_min_piece
        return single_qty

    def update_produces_quantity(self):
        single_qty = self.single_qty()
        for p in self.produces.all():
            KesOrderProduceItem.objects.filter(pk=p.id).update(quantity=p.piece * single_qty)


class KesOrderProduceItem(OrderItemBase):
    order = models.ForeignKey('KesOrder', on_delete=models.CASCADE, related_name='produce_items', blank=True, null=True,
                              verbose_name='对应界石单')
    raw_item = models.ForeignKey('KesOrderRawItem', on_delete=models.CASCADE, related_name='produces',
                                 verbose_name='原材料')
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE, verbose_name='product', blank=True,
                                null=True)
    thickness = models.DecimalField('厚度规格', max_digits=5, decimal_places=2)
    quantity = models.DecimalField('数量', decimal_places=2, max_digits=10, null=True, blank=True)

    class Meta:
        verbose_name = '界石单毛板项'
        # unique_together = ['thickness', 'raw_item']

    def save(self, *args, **kwargs):
        self.product = self.raw_item.product
        super(KesOrderProduceItem, self).save(*args, **kwargs)


# 更新毛板平方数的信用
@receiver(post_save, sender=KesOrderProduceItem, dispatch_uid='dis')
def post_save_update_produces_quantity(sender, **kwargs):
    kwargs['instance'].raw_item.update_produces_quantity()


@receiver(post_delete, sender=KesOrderProduceItem, dispatch_uid='sid')
def post_delete_update_produces_quantity(sender, **kwargs):
    kwargs['instance'].raw_item.update_produces_quantity()
