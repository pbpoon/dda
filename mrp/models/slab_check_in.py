from django.db import models
from django.urls import reverse

from mrp.models import MrpOrderAbstract, OrderItemBase
from public.fields import OrderField

UOM_CHOICES = (('t', '吨'), ('m3', '立方'), ('m2', '平方'))


class SlabCheckInOrder(MrpOrderAbstract):
    order = OrderField(order_str='PS', blank=True, verbose_name='单号', default='New', max_length=20)

    class Meta:
        verbose_name = "板材入库单"

    def get_location(self):
        return self.warehouse.get_production_location()

    def get_location_dest(self):
        return self.warehouse.get_main_location()

    def get_item_edit_url(self):
        return reverse('slab_check_in_item_edit')

    def get_absolute_url(self):
        return reverse('slab_check_in_detail', args=[self.id])

    def get_update_url(self):
        return reverse('slab_check_in_update', args=[self.id])


class SlabCheckInOrderRawItem(OrderItemBase):
    order = models.ForeignKey('SlabCheckInOrder', on_delete=models.CASCADE, related_name='raw_items',
                              verbose_name='板材入库单')

    class Meta:
        verbose_name = '板材入库单'

#
# class SlabCheckInOrderProduceItem(OrderItemBase):
#     order = models.ForeignKey('SlabCheckInOrder', on_delete=models.CASCADE, related_name='produce_items',
#                               verbose_name='板材入库单')
#     package_list = models.ForeignKey('product.PackageList', on_delete=models.SET_NULL, blank=True, null=True,
#                                      verbose_name='码单')
#     price = models.DecimalField('单价', max_digits=8, decimal_places=2, help_text='平方单价')
#
#     class Meta:
#         verbose_name = "板材入库单明细行"
#
#     def get_amount(self):
#         return self.price * self.quantity
#
#     def get_location_dest(self):
#         dest = self.location_dest if self.location_dest else self.order.location_dest
#         return dest
