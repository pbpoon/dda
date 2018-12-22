from _decimal import Decimal
import collections

from django.db import models
from django.db.models import Q
from django.urls import reverse

from invoice.models import CreateInvoice
from public.fields import OrderField, LineField
from public.models import OrderAbstract
from public.stock_operate import StockOperate

UOM_CHOICES = (('t', '吨'), ('m2', '平方'))


class SalesOrder(OrderAbstract):
    order = OrderField(order_str='SO', max_length=26, default='New', db_index=True, unique=True, verbose_name='订单号码', )
    partner = models.ForeignKey('partner.Partner', on_delete=models.CASCADE, limit_choices_to={'type': 'customer'},
                                verbose_name='客户名称')
    province = models.ForeignKey('partner.Province', verbose_name='省份', null=True, blank=True,
                                 on_delete=models.SET_NULL)
    city = models.ForeignKey('partner.City', verbose_name='城市', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = '销售订单'

    def __str__(self):
        return self.order

    def get_address(self):
        if self.province:
            address = self.province.name
            address += '/{}'.format(self.city if self.city else self.province.get_city()[0].name)
            return address
        return self.partner.get_address()

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

    def get_total(self):
        """
        template使用方式
        {% for key, item in object.get_total.items %}
        {{ key }}:{% if item.part %}{{ item.part }}夹 / {% endif %}{{ item.piece }}件 / {{ item.quantity }}{{ item.uom }}<br>
        {% endfor %}
        """
        d = collections.defaultdict(lambda: 0)
        total = {}
        for item in self.items.all():
            a = total.setdefault(item.product.get_type_display(), d)
            a['piece'] += item.piece
            a['quantity'] += item.quantity
            a['part'] += item.package_list.get_part() if item.package_list else 0
            a['uom'] = item.uom
        return total

    # 提货进度百分比
    def get_out_order_progress(self):
        out_order_total_quantity = sum(
            item.quantity for order in self.in_out_order.filter(state='done') for item in order.items.all())
        if self.get_piece() - sum(
                item.piece for order in self.in_out_order.filter(state='done') for item in order.items.all()) == 0:
            return 1
        number = (out_order_total_quantity / self.quantity)
        return number

    def confirm(self):
        is_done, msg = StockOperate(self, self.items.all()).reserve_stock()
        if is_done:
            self.state = 'confirm'
            self.save()
            self.invoices.all().update(state='draft')
            for invoice in self.get_invoices():
                invoice.state = 'draft'
                invoice.save()
            return is_done, msg
        return False, ''

    def draft(self):
        if self.state == 'confirm':
            if self.in_out_order.filter(Q(state='confirm') | Q(state='done')).exists():
                return False, '已有提货单为出库状态'
            is_done, msg = StockOperate(self, self.items.all()).reserve_stock(unlock=True)
            if is_done:
                self.state = 'draft'
                self.save()
            return is_done, msg
        return False, ''

    def get_invoices(self):
        return {invoice.order for item in self.items.all() for invoice in item.invoice_items.all().distinct()}

    @property
    def can_make_invoice(self):
        if sum(item.get_can_make_invoice_qty() for item in self.items.all()) > 0:
            return True
        return False

    def make_invoice(self):
        items_dict_list = [item.prepare_invoice_item() for item in self.items.all()]
        return CreateInvoice(self, self.partner, items_dict_list, type=1).invoice


class SalesOrderItem(models.Model):
    location = models.ForeignKey('stock.Location', related_name='%(class)s_location', verbose_name='库位',
                                 on_delete=models.DO_NOTHING, blank=True, null=True)
    location_dest = models.ForeignKey('stock.Location', related_name='%(class)s_location_dest', verbose_name='目标库位',
                                      on_delete=models.DO_NOTHING, blank=True, null=True)
    order = models.ForeignKey('SalesOrder', on_delete=models.CASCADE, related_name='items', verbose_name='销售订单')
    line = LineField(for_fields=['order'], blank=True, verbose_name='行')
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE, verbose_name='产品',
                                limit_choices_to={'type__in': ('block', 'slab')})
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

    def get_out_order_items(self):
        return (item for item in self.in_out_order_items.all() if item.state in ('confirm', 'done'))

    def can_delete(self):
        if list(self.get_out_order_items()):
            return False
        return True

    def get_can_make_invoice_qty(self):
        already_make_qty = sum(
            item.quantity for item in self.invoice_items.all() if item.state not in ('confirm', 'done'))
        if already_make_qty:
            return self.quantity - already_make_qty
        return self.quantity

    def prepare_invoice_item(self):
        return {'item': str(self.product), 'quantity': self.get_can_make_invoice_qty(), 'price': self.price,
                'sales_order_item': self}
