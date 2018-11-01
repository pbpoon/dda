from decimal import Decimal

from datetime import datetime
from django.db import models
from mrp.models import OrderAbstract
from purchase.fields import LineField
from django.contrib.auth.models import User
from django.shortcuts import reverse

CURRENCY_CHOICE = (
    ('USD', u'$美元'),
    ('CNY', u'￥人民币'),
    ('EUR', u'€欧元'),
)
UOM_CHOICES = (('t', '吨'), ('m3', '立方'))


class PurchaseOrder(OrderAbstract):
    currency = models.CharField('货币', choices=CURRENCY_CHOICE, max_length=10)
    uom = models.CharField('计量单位', null=False, choices=UOM_CHOICES, max_length=10)

    class Meta:
        verbose_name = '采购订单'
        ordering = ['-order']

    def get_absolute_url(self):
        return reverse('purchase_order_detail', args=[self.id])

    def save(self, *args, **kwargs):
        # 格式为 IM1703001
        date_str = datetime.now().strftime('%y%m')
        if self.order == 'New':
            last_record = self.__class__.objects.last()
            if last_record:
                last_order = last_record.order
                if date_str in last_order[2:6]:
                    self.order = 'PO' + str(int(last_order[2:9]) + 1)
                else:
                    self.order = 'PO' + date_str + '001'  # 新月份
            else:
                self.order = 'PO' + date_str + '001'  # 新记录
        super(OrderAbstract, self).save(*args, **kwargs)

    def get_quantity(self):
        return sum(item.get_quantity() for item in self.items.all())

    def get_amount(self):
        return sum(item.get_amount() for item in self.items.all())


class PurchaseOrderItem(models.Model):
    # line = LineField(for_fields=['order'], blank=True, verbose_name='行')
    name = models.CharField('编号', max_length=20, unique=True)
    type = models.CharField('类型', max_length=10, default='block')
    # uom = models.CharField('计量单位', null=False, choices=UOM_CHOICES, max_length=10, default='t')
    order = models.ForeignKey('PurchaseOrder', on_delete=models.CASCADE, related_name='items', verbose_name='订单',
                              blank=True, null=True)
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE, verbose_name='编号', blank=True, null=True)
    price = models.DecimalField('单价', max_digits=8, decimal_places=2)
    uom = models.CharField('计量单位', null=False, choices=UOM_CHOICES, max_length=10, default='t')
    weight = models.DecimalField('重量', max_digits=5, decimal_places=2, null=True)
    long = models.IntegerField('长', null=True, blank=True)
    width = models.IntegerField('宽', null=True, blank=True)
    height = models.IntegerField('高', null=True, blank=True)
    m3 = models.DecimalField('立方', null=True, max_digits=5, decimal_places=2, blank=True)
    entry = models.ForeignKey(User, related_name='%(class)s_entry',
                              verbose_name='登记人', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = '采购订单行'
        ordering = ['order']

    def get_quantity(self):
        return self.weight if self.uom == 't' else self.m3

    def get_amount(self):
        quantity = self.weight if self.uom == 't' else self.m3
        return Decimal('{0:.2f}'.format(quantity * self.price))
