from _decimal import Decimal
import collections

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models import Q
from django.urls import reverse

from invoice.models import CreateInvoice
from public.fields import OrderField, LineField
from public.models import OrderAbstract, HasChangedMixin, OrderItemSaveCreateCommentMixin
from public.stock_operate import StockOperate
from .partner import Customer

UOM_CHOICES = (('t', '吨'), ('m2', '平方'))


class SalesOrder(OrderAbstract):
    order = OrderField(order_str='SO', max_length=26, default='New', db_index=True, unique=True, verbose_name='订单号码', )
    partner = models.ForeignKey('partner.Customer', on_delete=models.CASCADE, verbose_name='客户名称',
                                related_name='sales_order')
    province = models.ForeignKey('partner.Province', verbose_name='省份', null=True, blank=True,
                                 on_delete=models.SET_NULL)
    city = models.ForeignKey('partner.City', verbose_name='城市', null=True, blank=True, on_delete=models.SET_NULL)
    invoices = GenericRelation('invoice.SalesInvoice')

    class Meta:
        verbose_name = '销售订单'
        permissions = (('can_audit', '审核'),)
        ordering = ['-date', '-created']

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

    def get_delete_url(self):
        return reverse('sales_order_delete', args=[self.id])

    def get_list_url(self):
        return reverse('sales_order_list', args=[self.id])

    @property
    def amount(self):
        return sum(item.amount for item in self.items.all())

    @property
    def due_amount(self):
        return self.amount - self.confirm_amount

    @property
    def confirm_amount(self):
        return sum(invoice.confirm_amount for invoice in self.invoices.all())
        # return sum(invoice.amount for item in self.items.all() for invoice in
        #            item.invoice_items.filter(order__state='done').distinct())

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

        total = {}
        for item in self.items.all():
            d = collections.defaultdict(lambda: 0)
            a = total.setdefault(item.product.get_type_display(), d)
            a['piece'] += item.piece if item.piece else 0
            a['quantity'] += item.quantity if item.quantity else 0
            a['part'] += item.package_list.get_part() if item.package_list else 0
            a['uom'] = item.uom
        return total

    # 提货进度百分比
    def get_out_order_percentage(self):
        out_order_total_quantity = sum(
            order.get_quantity() for order in self.in_out_order.filter(state='done'))
        # if self.get_piece() - sum(
        #         order.get_ for order in self.in_out_order.filter(state='done') for item in order.items.all()) == 0:
        #     return 1
        if self.quantity != 0:
            number = (out_order_total_quantity / self.quantity)
        else:
            number = 0
        return number

    def get_can_in_out_order_qty(self):
        quantity, piece, part = 0, 0, 0
        for item in self.items.all():
            qty = item.get_can_in_out_order_qty()
            if qty['piece'] > 0:
                quantity += qty['quantity']
                piece += qty['piece']
                part += qty['part']
        return {'quantity': quantity, 'piece': piece, 'part': part}

    def confirm(self, **kwargs):
        is_done, msg = StockOperate(self, self.items.all()).reserve_stock()
        if is_done:
            self.state = 'confirm'
            self.save()
            self.create_comment(**kwargs)
            self.make_invoice()
            comment = '更新<a href="%s">%s</a>状态:%s, 修改本账单' % (self.get_absolute_url(), self, self.state)
            for invoice in self.invoices.all():
                if invoice.state != 'draft':
                    continue
                invoice.state = 'confirm'
                invoice.save()
                invoice.create_comment(**{'comment': comment})
            return is_done, msg
        return False, msg

    def done(self, **kwargs):
        # if self.get_can_in_out_order_qty()['piece'] == 0 and (int(self.amount) - int(self.due_amount)) <= 0:
        if self.get_can_in_out_order_qty()['piece'] == 0 and self.due_amount <= 0:
            self.state = 'done'
            self.save()
            if kwargs.get('comment'):
                kwargs['comment'] += '本订单已全部提货，完成收款'
        self.create_comment(**kwargs)
        if self.state == 'done':
            return True, ''
        return False, ''

    def draft(self, **kwargs):
        is_done, msg = True, ''
        if self.state == 'confirm':
            if self.in_out_order.filter(Q(state='confirm') | Q(state='done')).exists():
                return False, '已有提货单为出库状态'
            is_done, msg = StockOperate(self, self.items.all()).reserve_stock(unlock=True)
        if self.state == 'done':
            is_done, msg = False, '不能把已完成的订单设置为：取消'
        if is_done:
            self.state = 'draft'
            self.save()
            self.create_comment(**kwargs)
            comment = '更新<a href="%s">%s</a>状态:%s, 修改本账单' % (self.get_absolute_url(), self, self.state)
            for invoice in self.invoices.all():
                invoice.state = 'draft'
                invoice.save()
                invoice.create_comment(**{'comment': comment})
        return is_done, msg

    def cancel(self, **kwargs):
        is_done, msg = True, ''
        if self.state == 'confirm':
            if self.in_out_order.filter(Q(state='confirm') | Q(state='done')).exists():
                return False, '已有提货单为出库状态'
            is_done, msg = StockOperate(self, self.items.all()).reserve_stock(unlock=True)
        if self.state == 'done':
            is_done, msg = False, '不能把已完成的订单设置为：取消'
        if is_done:
            self.state = 'cancel'
            self.save()
            self.create_comment(**kwargs)
            comment = '更新<a href="%s">%s</a>状态:%s, 修改本账单' % (self.get_absolute_url(), self, self.state)
            for invoice in self.invoices.all():
                invoice.state = 'cancel'
                invoice.save()
                invoice.create_comment(**{'comment': comment})
        return is_done, msg

    def _get_invoice_usage(self):
        return '销售货款'

    # @property
    # def invoices(self):
    #     from invoice.models import SalesInvoice
    #     invoices = SalesInvoice.objects.none()
    #     for item in self.items.all():
    #         for invoice in item.invoice_items.all():
    #             invoices |= invoice.order
    #     return invoices

    @property
    def can_make_invoice_amount(self):
        return sum(item.get_can_make_invoice_amount() for item in self.items.all())

    def make_invoice(self):
        items_dict = {}
        for item in self.items.all():
            # invoice_line = item.prepare_invoice_item()
            # if invoice_line in items_dict:
            #     items_dict[invoice_line]['quantity'] += invoice_line['quantity']
            # else:
            #     items_dict.update(item.prepare_invoice_item())
            items_dict.update(item.prepare_invoice_item())
        state = self.state if self.state != 'done' else 'confirm'
        return CreateInvoice(self, self.partner, items_dict, type=1, state=state).invoice


class SalesOrderItem(OrderItemSaveCreateCommentMixin, models.Model):
    location = models.ForeignKey('stock.Location', related_name='%(class)s_location', verbose_name='库位',
                                 on_delete=models.DO_NOTHING, blank=True, null=True)
    location_dest = models.ForeignKey('stock.Location', related_name='%(class)s_location_dest', verbose_name='目标库位',
                                      on_delete=models.DO_NOTHING, blank=True, null=True)
    order = models.ForeignKey('SalesOrder', on_delete=models.CASCADE, related_name='items', verbose_name='销售订单')
    line = LineField(for_fields=['order'], blank=True, verbose_name='行')
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE, verbose_name='产品',
                                limit_choices_to={'type__in': ('block', 'slab')}, related_name='sales_order_item')
    piece = models.IntegerField('件', blank=True, null=True)
    quantity = models.DecimalField('数量', decimal_places=2, max_digits=10, blank=True, null=True)
    uom = models.CharField('计量单位', null=False, choices=UOM_CHOICES, max_length=10, default='t')
    price = models.DecimalField('单价', max_digits=8, decimal_places=2)
    package_list = models.ForeignKey('product.PackageList', on_delete=models.SET_NULL, blank=True, null=True,
                                     verbose_name='码单')
    invoice_items = GenericRelation('invoice.InvoiceItem')

    monitor_fields = ['line', 'product', 'price', 'quantity', 'uom', 'piece']

    class Meta:
        verbose_name = '销售订单行'
        ordering = ('line',)

    @property
    def amount(self):
        if self.quantity:
            return Decimal('{0:.0f}'.format(self.quantity * self.price))
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
            item.quantity for item in self.invoice_items.all() if item.state in ('confirm', 'done'))
        if already_make_qty:
            return self.quantity - already_make_qty
        return self.quantity

    def prepare_invoice_item(self):
        return {str(self.product): {'item': str(self.product), 'from_order_item': self,
                                    'quantity': self.get_can_make_invoice_qty(),
                                    'line': self.line, 'price': self.price}}

    def get_can_make_invoice_amount(self):
        return self.get_can_make_invoice_qty() * self.price

    def get_in_out_order_qty(self):
        quantity, piece, part = 0, 0, 0
        for item in self.in_out_order_items.all():
            if item.state in ('confirm', 'done'):
                quantity += item.quantity
                piece += item.piece
                part += item.package_list.get_part() if item.package_list else 0
        return {'quantity': quantity, 'piece': piece, 'part': part}

    def get_can_in_out_order_qty(self):
        in_out_order_qty = self.get_in_out_order_qty()
        quantity = self.quantity - in_out_order_qty['quantity']
        piece = self.piece - in_out_order_qty['piece']
        part = self.package_list.get_part() - in_out_order_qty['part'] if self.package_list else 0
        return {'quantity': quantity, 'piece': piece, 'part': part}
