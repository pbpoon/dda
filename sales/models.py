from _decimal import Decimal

from django.db import models
from django.urls import reverse

from public.fields import OrderField, LineField
from public.models import OrderAbstract

UOM_CHOICES = (('t', '吨'), ('m2', '平方'))


class SalesOrder(OrderAbstract):
    order = OrderField(order_str='SO', max_length=26, default='New', db_index=True, unique=True, verbose_name='订单号码', )
    partner = models.ForeignKey('partner.Partner', on_delete=models.SET_NULL, null=True, blank=True,
                                limit_choices_to={'type': 'customer'},
                                verbose_name='客户名称')

    class Meta:
        verbose_name = '销售订单'

    def get_absolute_url(self):
        return reverse('sales_order_detail', args=[self.id])

    def get_item_edit_url(self):
        return reverse('sales_order_item_edit')

    def get_update_url(self):
        return reverse('sales_order_update', args=[self.id])

    @property
    def amount(self):
        return sum(item.amount for item in self.items.all())

    def __str__(self):
        return self.order


class SalesOrderItem(models.Model):
    order = models.ForeignKey('SalesOrder', on_delete=models.CASCADE, related_name='items', verbose_name='销售订单')
    line = LineField(for_fields=['order'], blank=True, verbose_name='行')
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE, verbose_name='product')
    piece = models.IntegerField('件', default=1)
    quantity = models.DecimalField('数量', decimal_places=2, max_digits=10)
    uom = models.CharField('计量单位', null=False, choices=UOM_CHOICES, max_length=10, default='t')
    price = models.DecimalField('单价', max_digits=8, decimal_places=2, help_text='立方单价', null=True, blank=True)
    package_list = models.ForeignKey('product.PackageList', on_delete=models.SET_NULL, blank=True, null=True,
                                     verbose_name='码单')

    class Meta:
        verbose_name = '销售订单行'

    @property
    def amount(self):
        return Decimal('{0:.2f}'.format(self.quantity * self.price))

