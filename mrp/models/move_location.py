from django.db import models
from django.urls import reverse

from mrp.models import MrpOrderAbstract, OrderItemBase
from public.fields import OrderField

UOM_CHOICES = (('t', '吨'), ('m3', '立方'), ('m2', '平方'))


class MoveLocationOrder(MrpOrderAbstract):
    partner = models.ForeignKey('partner.Partner', on_delete=models.SET_NULL, null=True, blank=True,
                                limit_choices_to={'type': 'supplier'},
                                verbose_name='运输单位', help_text='账单[对方]对应本项。如果为空，则不会生产账单')
    order = OrderField(order_str='MO', blank=True, verbose_name='单号', default='New', max_length=20)
    warehouse = models.ForeignKey('stock.Warehouse', on_delete=models.CASCADE, verbose_name='移出仓库',
                                  related_name='move_out_warehouse')
    warehouse_dest = models.ForeignKey('stock.Warehouse', on_delete=models.CASCADE, verbose_name='接收仓库',
                                       related_name='move_in_warehouse')

    class Meta:
        verbose_name = '移库单'

    def get_location(self):
        return self.warehouse.get_main_location()

    def get_location_dest(self):
        return self.warehouse_dest.get_main_location()

    def get_create_item_url(self):
        return reverse('move_location_order_item_create', args=[self.id])

    def get_absolute_url(self):
        return reverse('move_location_order_detail', args=[self.id])

    def get_update_url(self):
        return reverse('move_location_order_update', args=[self.id])

    def get_stock(self):
        from mrp.models import StockOperate
        return StockOperate(order=self, items=self.items.all())

    def done(self):
        stock = self.get_stock()
        if self.state == 'confirm':
            is_done, msg = stock.reserve_stock(unlock=True)
            if not is_done:
                return is_done, msg
        is_done, msg = stock.handle_stock()
        if is_done:
            self.state = 'done'
            self.save()
        return is_done, msg

    def confirm(self):
        stock = self.get_stock()
        is_done, msg = stock.reserve_stock()
        if is_done:
            self.state = 'confirm'
            self.save()
        return is_done, msg

    def draft(self):
        stock = self.get_stock()
        if self.state == 'confirm':
            is_done, msg = stock.reserve_stock(unlock=True)
            if is_done:
                self.state = 'draft'
                self.save()
            return is_done, msg
        return False, ''


class MoveLocationOrderItem(OrderItemBase):
    location = models.ForeignKey('stock.Location', related_name='%(class)s_location', verbose_name='库位',
                                 on_delete=models.DO_NOTHING, blank=True, null=True,
                                 limit_choices_to={'is_virtual': False})
    location_dest = models.ForeignKey('stock.Location', related_name='%(class)s_location_dest', verbose_name='目标库位',
                                      on_delete=models.DO_NOTHING, blank=True, null=True,
                                      limit_choices_to={'is_virtual': False})
    order = models.ForeignKey('MoveLocationOrder', on_delete=models.CASCADE, related_name='items', blank=True,
                              null=True,
                              verbose_name='对应移库单')
    package_list = models.ForeignKey('product.PackageList', on_delete=models.SET_NULL, blank=True, null=True,
                                     verbose_name='码单')

    class Meta:
        verbose_name = '移库单明细行'

    def get_location(self):
        loc = self.location if self.location else self.order.location
        return loc

    def get_location_dest(self):
        dest = self.location_dest if self.location_dest else self.order.location_dest
        return dest
