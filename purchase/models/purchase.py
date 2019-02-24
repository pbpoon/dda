import collections
from decimal import Decimal

from django.contrib.contenttypes.fields import GenericRelation

from invoice.models import CreateInvoice
from product.models import Product, Batch
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
    partner = models.ForeignKey('partner.Supplier', on_delete=models.CASCADE, related_name='purchase_order',
                                verbose_name='供应商')
    order = OrderField(order_str='PO', max_length=10, default='New', db_index=True, unique=True, verbose_name='订单号码', )
    currency = models.CharField('货币', choices=CURRENCY_CHOICE, max_length=10)
    uom = models.CharField('计量单位', null=False, choices=UOM_CHOICES, max_length=10)
    batch = models.CharField('批次', max_length=10, blank=True, null=True, help_text='如果不填，则采取"-"号前或编号前2位作为批次号')
    category = models.ForeignKey('product.Category', on_delete=models.CASCADE, verbose_name='品种分类')
    quarry = models.ForeignKey('product.Quarry', on_delete=models.CASCADE, verbose_name='矿口')

    invoices = GenericRelation('invoice.PurchaseInvoice')

    class Meta:
        verbose_name = '采购订单'
        ordering = ['-order']

    def __str__(self):
        return self.order

    def get_absolute_url(self):
        return reverse('purchase_order_detail', args=[self.id])

    def get_quantity(self):
        return sum(item.get_quantity() for item in self.items.all())

    def get_total(self):
        """
        template使用方式
        {% for key, item in object.get_total.items %}
        {{ key }}:{% if item.part %}{{ item.part }}夹 / {% endif %}{{ item.piece }}件 / {{ item.quantity }}{{ item.uom }}<br>
        {% endfor %}
        """
        if not self.items.all():
            return
        total = {}
        for item in self.items.all():
            if not item.product:
                continue
            d = collections.defaultdict(lambda: 0)
            a = total.setdefault(item.product.get_type_display(), d)
            a['piece'] += item.piece
            a['quantity'] += item.quantity
            # d['part'] += item.package_list.get_part() if item.package_list else 0
            a['uom'] = item.uom
            # total.setdefault(item.product.get_type_display(), {}).update(d)
        return total

    @property
    def amount(self):
        return self.get_amount()

    def get_amount(self):
        return sum(item.get_amount() for item in self.items.all())

    def get_create_item_url(self):
        return reverse('purchase_order_item_create', args=[self.id])

    def get_update_url(self):
        return reverse('purchase_order_update', args=[self.id])

    def confirm(self, **kwargs):
        for item in self.items.all():
            item.confirm()
        self.state = 'confirm'
        self.save()
        # 日后生产invoice
        self.create_comment(**kwargs)
        msg = '设置订单%s设置成 %s 状态' % (self.order, self.get_state_display())
        return True, msg

    def draft(self, **kwargs):
        for item in self.items.all():
            item.draft()
        self.state = 'draft'
        self.save()
        self.create_comment(**kwargs)
        msg = '设置订单%s设置成 %s 状态' % (self.order, self.get_state_display())
        return True, msg

    def done(self, **kwargs):
        self.create_comment(**kwargs)
        return True, ''

    def _get_invoice_usage(self):
        return '采购货款'

    # @property
    # def invoices(self):
    #     from invoice.models import PurchaseInvoice
    #     # invoices = set(self.invoices.all())
    #     invoices = PurchaseInvoice.objects.none()
    #     for item in self.items.all():
    #         for item in item.invoice_items.all():
    #             invoices |= item.order
    #     # invoices |= {invoice.order for item in self.items.all() for invoice in item.invoice_items.all().distinct()}
    #     return invoices

    @property
    def can_make_invoice_amount(self):
        return sum(item.get_can_make_invoice_amount() for item in self.items.all())

    def make_invoice(self):
        items_dict = {}
        for item in self.items.all():
            items_dict.update(item.prepare_invoice_item())
        state = self.state if self.state != 'done' else 'confirm'
        return CreateInvoice(self, self.partner, items_dict, type=-1, state=state).invoice


class PurchaseOrderItem(models.Model):
    line = LineField(for_fields=['order'], blank=True, verbose_name='行')
    name = models.CharField('编号', max_length=20)
    type = models.CharField('类型', max_length=10, default='block')
    batch = models.CharField('批次', max_length=10, blank=True, null=True)
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
    invoice_items = GenericRelation('invoice.InvoiceItem')

    class Meta:
        verbose_name = '采购订单行'
        ordering = ['line']
        unique_together = (('order', 'name'), ('order', 'name', 'product'))

    def get_quantity(self):
        return self.weight if self.uom == 't' else self.m3

    @property
    def category(self):
        return self.order.category

    @property
    def quarry(self):
        return self.order.quarry

    @property
    def amount(self):
        return self.get_amount()

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

    def prepare_block_default(self):
        block_fields = ('name', 'category', 'quarry', 'weight', 'long', 'width', 'height', 'm3', 'uom')
        kwargs = {f.name: getattr(self, f.name) for f in self._meta.fields if f.name in block_fields}
        batch_name = self.batch
        batch, _ = Batch.objects.get_or_create(name=batch_name)
        kwargs['batch'] = batch
        kwargs['category'] = self.category
        kwargs['quarry'] = self.quarry
        return kwargs

    def confirm(self):
        self.product = Product.create(type='block', name=self.name, defaults=self.prepare_block_default())
        # 日后product action 添加action记录
        self.product.activate = True
        return self.save()

    def draft(self):
        self.product.activate = False
        return self.save()

    def get_can_make_invoice_qty(self):
        already_make_qty = sum(
            item.quantity for item in self.invoice_items.all() if item.state in ('confirm', 'done'))
        if already_make_qty:
            return self.quantity - already_make_qty
        return self.quantity

    def get_can_make_invoice_amount(self):
        return self.get_can_make_invoice_qty() * self.price

    def prepare_invoice_item(self):
        return {str(self.product): {'item': str(self.product), 'from_order_item': self,
                                    'quantity': self.get_can_make_invoice_qty(), 'uom': self.uom,
                                    'line': self.line, 'price': self.price}}

    def get_can_in_out_order_qty(self):
        quantity, piece, part = 0, 0, 0
        for item in self.in_out_order_items.all():
            if item.state in ('confirm', 'done'):
                quantity += item.quantity
                piece += item.piece
                part += item.package_list.get_part() if item.package_list else 0
        return {'quantity': quantity, 'piece': piece, 'part': part}
