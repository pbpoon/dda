from _decimal import Decimal

from django.db import models
from django.urls import reverse

from public.fields import OrderField, LineField
from public.models import OrderAbstract

UOM_CHOICES = (('t', '吨'), ('m2', '平方'))


class SalesOrder(OrderAbstract):
    order = OrderField(order_str='SO', max_length=26, default='New', db_index=True, unique=True, verbose_name='订单号码', )
    partner = models.ForeignKey('partner.Partner', on_delete=models.CASCADE, limit_choices_to={'type': 'customer'},
                                verbose_name='客户名称')
    province = models.ForeignKey('partner.Province', verbose_name='省份', null=True, blank=True, on_delete=models.SET_NULL)
    city = models.ForeignKey('partner.City', verbose_name='城市', null=True, blank=True, on_delete=models.SET_NULL)
    area = models.ForeignKey('partner.Area', verbose_name='地区', null=True, blank=True, on_delete=models.SET_NULL)

    def get_address(self):
        if self.province:
            address = self.province.name
            address += '/{}'.format(self.city if self.city else self.province.get_city()[0].name)
            address += '/{}'.format(self.area if self.area else self.province.get_city()[0].get_area()[0])
            return address
        return self.partner.get_address()

    class Meta:
        verbose_name = '销售订单'

    def get_absolute_url(self):
        return reverse('sales_order_detail', args=[self.id])

    def get_create_item_url(self):
        return reverse('sales_order_item_create', args=[self.id])

    def get_update_url(self):
        return reverse('sales_order_update', args=[self.id])

    @property
    def amount(self):
        return sum(item.amount for item in self.items.all())

    def get_piece(self):
        return sum(item.piece for item in self.items.all() if item.piece)

    @property
    def quantity(self):
        return sum(item.quantity for item in self.items.all() if item.quantity)

    def get_out_order_progress(self):
        out_order_total_quantity = sum(
            item.quantity for order in self.in_out_order.filter(state='done') for item in order.items.all())
        if self.get_piece() - sum(
                item.piece for order in self.in_out_order.filter(state='done') for item in order.items.all()) == 0:
            return 1
        number = (out_order_total_quantity / self.quantity)
        return number

    def __str__(self):
        return self.order


class SalesOrderItem(models.Model):
    location = models.ForeignKey('stock.Location', related_name='%(class)s_location', verbose_name='库位',
                                 on_delete=models.DO_NOTHING, blank=True, null=True)
    location_dest = models.ForeignKey('stock.Location', related_name='%(class)s_location_dest', verbose_name='目标库位',
                                      on_delete=models.DO_NOTHING, blank=True, null=True)
    order = models.ForeignKey('SalesOrder', on_delete=models.CASCADE, related_name='items', verbose_name='销售订单')
    line = LineField(for_fields=['order'], blank=True, verbose_name='行')
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE, verbose_name='product')
    piece = models.IntegerField('件', blank=True, null=True)
    quantity = models.DecimalField('数量', decimal_places=2, max_digits=10, blank=True, null=True)
    uom = models.CharField('计量单位', null=False, choices=UOM_CHOICES, max_length=10, default='t')
    price = models.DecimalField('单价', max_digits=8, decimal_places=2)
    package_list = models.ForeignKey('product.PackageList', on_delete=models.SET_NULL, blank=True, null=True,
                                     verbose_name='码单')

    class Meta:
        verbose_name = '销售订单行'
        ordering = ('line',)

    @property
    def amount(self):
        if self.quantity:
            return Decimal('{0:.2f}'.format(self.quantity * self.price))
        return 0

    def save(self, *args, **kwargs):
        self.location_dest = self.order.partner.get_location()
        self.uom = self.product.get_uom()
        if self.package_list:
            self.piece = self.package_list.get_piece()
            self.quantity = self.package_list.get_quantity()
        super().save(*args, **kwargs)
