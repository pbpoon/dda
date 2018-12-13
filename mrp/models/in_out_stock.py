from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.db import models
from django.urls import reverse

from mrp.models import MrpOrderAbstract, OrderItemBase
from public.fields import OrderField

UOM_CHOICES = (('t', '吨'), ('m3', '立方'), ('m2', '平方'))
OPERATION_TYPE = (('in', '入库'), ('out', '出库'))


class InOutOrder(MrpOrderAbstract):
    type = models.CharField('出入库类型', choices=OPERATION_TYPE, max_length=10)
    order = OrderField(order_str='IO', blank=True, verbose_name='单号', default='New', max_length=20)
    counter = models.IntegerField('货柜数', blank=True, null=True)
    purchase_order = models.ForeignKey('purchase.PurchaseOrder', on_delete=models.CASCADE, verbose_name='采购单',
                                       related_name='in_out_order', blank=True, null=True)
    sales_order = models.ForeignKey('sales.SalesOrder', on_delete=models.CASCADE, verbose_name='销售单',
                                    related_name='in_out_order', blank=True, null=True)
    warehouse = models.ForeignKey('stock.Warehouse', on_delete=models.CASCADE, verbose_name='仓库')
    cart_number = models.CharField('车牌/柜号', max_length=20, blank=True, null=True)
    pickup_staff = models.CharField('提货人', max_length=12, blank=True, null=True)

    class Meta:
        verbose_name = '出入库操作'

    @property
    def from_order(self):
        return self.sales_order or self.purchase_order

    def __str__(self):
        return self.full_order

    @property
    def full_order(self):
        from_order = self.purchase_order or self.sales_order
        count = from_order.in_out_order.filter(state__in=('confirm', 'done')).count()
        if count > 1:
            last_display = '({})'.format(count)
        else:
            last_display = ''
        return '{}/{}{}'.format(from_order, self.get_type_display(), last_display)

    def get_absolute_url(self):
        return reverse('in_out_order_detail', args=[self.id])

    def get_create_item_url(self):
        return reverse('in_out_order_item_create', args=[self.id])

    def get_delete_url(self):
        return reverse('in_out_order_delete', args=[self.id])

    def get_location(self):
        if self.type == 'in':
            loc = self.purchase_order.partner.get_location()
        else:
            loc = self.warehouse.get_main_location()
        return loc

    def get_location_dest(self):
        if self.type == 'out':
            loc = self.sales_order.partner.get_location()
        else:
            loc = self.warehouse.get_main_location()
        return loc

    # def get_update_url(self):
    #     return reverse('in_out_order_item_create', args=[self.id])


class InOutOrderItem(OrderItemBase):
    order = models.ForeignKey('InOutOrder', on_delete=models.CASCADE, related_name='items', verbose_name='对应订单')
    package_list = models.ForeignKey('product.PackageList', on_delete=models.SET_NULL, blank=True, null=True,
                                     verbose_name='码单')
    expenses = GenericRelation('mrp.Expenses')

    class Meta:
        verbose_name = '出入库操作明细行'

    def save(self, *args, **kwargs):
        if self.package_list:
            self.piece = self.package_list.get_piece()
            self.quantity = self.package_list.get_quantity()
        super().save(*args, **kwargs)
