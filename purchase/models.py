from decimal import Decimal

from product.models import Product
from public.models import OrderAbstract
from public.fields import OrderField, LineField
from datetime import datetime
from django.db import models
from django.contrib.auth.models import User
from django.shortcuts import reverse

CURRENCY_CHOICE = (
    ('USD', u'$美元'),
    ('CNY', u'￥人民币'),
    ('EUR', u'€欧元'),
)
UOM_CHOICES = (('t', '吨'), ('m3', '立方'))


class PurchaseOrder(OrderAbstract):
    partner = models.ForeignKey('partner.Partner', on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name='业务伙伴', limit_choices_to={'type': 'supplier', 'is_production': False})
    order = OrderField(order_str='PO', max_length=10, default='New', db_index=True, unique=True, verbose_name='订单号码', )
    currency = models.CharField('货币', choices=CURRENCY_CHOICE, max_length=10)
    uom = models.CharField('计量单位', null=False, choices=UOM_CHOICES, max_length=10)

    class Meta:
        verbose_name = '采购订单'
        ordering = ['-order']

    def get_absolute_url(self):
        return reverse('purchase_order_detail', args=[self.id])

    def get_quantity(self):
        return sum(item.get_quantity() for item in self.items.all())

    def get_amount(self):
        return sum(item.get_amount() for item in self.items.all())

    def get_create_item_url(self):
        return reverse('purchase_order_item_create')

    def get_update_url(self):
        return reverse('purchase_order_update', args=[self.id])


class PurchaseOrderItem(models.Model):
    line = LineField(for_fields=['order'], blank=True, verbose_name='行')
    name = models.CharField('编号', max_length=20, unique=True)
    type = models.CharField('类型', max_length=10, default='block')
    order = models.ForeignKey('PurchaseOrder', on_delete=models.CASCADE, related_name='items', verbose_name='订单')
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE, verbose_name='编号', blank=True, null=True)
    price = models.DecimalField('单价', max_digits=8, decimal_places=2)
    piece = models.IntegerField('件', default=1)
    quantity = models.DecimalField('数量', max_digits=8, decimal_places=2)
    uom = models.CharField('计量单位', choices=UOM_CHOICES, max_length=10, default='t')
    weight = models.DecimalField('重量', max_digits=5, decimal_places=2, null=True, blank=True)
    long = models.IntegerField('长', null=True, blank=True)
    width = models.IntegerField('宽', null=True, blank=True)
    height = models.IntegerField('高', null=True, blank=True)
    m3 = models.DecimalField('立方', null=True, max_digits=5, decimal_places=2, blank=True)

    class Meta:
        verbose_name = '采购订单行'
        ordering = ['order']

    def get_quantity(self):
        return self.weight if self.uom == 't' else self.m3

    def get_amount(self):
        return Decimal('{0:.2f}'.format(self.quantity * self.price))

    def get_size(self):
        return '%sx%sx%s' % (self.long, self.weight, self.height)

    def save(self, *args, **kwargs):
        self.uom = self.order.uom
        self.quantity = self.get_quantity()
        if not self.weight and not self.m3:
            raise ValueError('重量及立方不能同时为空')
        super().save(*args, **kwargs)

    def confirm(self):
        block_fields = ('name', 'batch', 'category', 'quarry', 'weight', 'long', 'width', 'height', 'm3', 'uom')
        p_kwarg = {f.name: getattr(self, f.name) for f in self._meta.fields if f.name in block_fields}
        self.product = Product.create(type='block', defaults=p_kwarg)
        # 日后product action 添加action记录
        return self.save()
