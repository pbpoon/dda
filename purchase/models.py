from decimal import Decimal
from .fields import OrderField
from datetime import datetime
from django.db import models
from purchase.fields import LineField
from django.contrib.auth.models import User
from django.shortcuts import reverse
from django.contrib.contenttypes.fields import GenericRelation

CURRENCY_CHOICE = (
    ('USD', u'$美元'),
    ('CNY', u'￥人民币'),
    ('EUR', u'€欧元'),
)
UOM_CHOICES = (('t', '吨'), ('m3', '立方'))

STATE_CHOICES = (
    ('draft', '草稿'),
    ('confirm', '确认'),
    ('cancel', '取消'),
)


class OrderAbstract(models.Model):
    state = models.CharField('状态', choices=STATE_CHOICES, max_length=20, default='draft')
    order = OrderField(order_str=None, max_length=26, default='New', db_index=True, unique=True, verbose_name='订单号码', )
    date = models.DateField('日期')
    created = models.DateField('创建日期', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)
    handler = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='经办人',
                                related_name='%(class)s_handler')
    entry = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='登记人',
                              related_name='%(class)s_entry')
    partner = models.ForeignKey('partner.Partner', on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name='业务伙伴')
    comments = GenericRelation('comment.Comment')
    invoices = GenericRelation('invoice.OrderInvoiceThrough')

    class Meta:
        abstract = True
        ordering = ['-created']

    def get_quantity(self):
        return sum(item.quantity for item in self.items.all())

    def get_amount(self):
        return sum(item.get_amount() for item in self.items.all())


class PurchaseOrder(OrderAbstract):
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

    def get_size(self):
        return '%sx%sx%s' % (self.long, self.weight, self.height)
