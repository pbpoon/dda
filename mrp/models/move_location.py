from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.urls import reverse

from mrp.models import MrpOrderAbstract, OrderItemBase
from public.fields import OrderField

UOM_CHOICES = (('t', '吨'), ('m3', '立方'), ('m2', '平方'))


class MoveLocationOrder(MrpOrderAbstract):
    partner = models.ForeignKey('partner.Partner', on_delete=models.SET_NULL, null=True, blank=True,
                                limit_choices_to={'type__in': 'service'},
                                verbose_name='运输单位', help_text='账单[对方]对应本项。如果为空，则不会生产账单')
    order = OrderField(order_str='MO', blank=True, verbose_name='单号', default='New', max_length=20)
    warehouse = models.ForeignKey('stock.Warehouse', on_delete=models.CASCADE, verbose_name='移出仓库',
                                  related_name='move_out_warehouse')
    warehouse_dest = models.ForeignKey('stock.Warehouse', on_delete=models.CASCADE, verbose_name='接收仓库',
                                       related_name='move_in_warehouse')

    class Meta:
        verbose_name = '移库单'

    def _get_invoice_usage(self):
        return '运输费'

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
        from public.stock_operate import StockOperate
        return StockOperate(order=self, items=self.items.all())

    def get_expenses_amount(self):
        return sum(item.get_expenses_amount() for item in self.items.all())

    def done(self, **kwargs):
        stock = self.get_stock()
        if self.state == 'confirm':
            is_done, msg = stock.reserve_stock(unlock=True)
            if not is_done:
                return is_done, msg
        is_done, msg = stock.handle_stock()
        if is_done:
            self.state = 'done'
            self.save()
            self.create_comment(**kwargs)
            self.make_expenses_invoice()
        return is_done, msg

    def confirm(self, **kwargs):
        stock = self.get_stock()
        is_done, msg = stock.reserve_stock()
        if is_done:
            self.state = 'confirm'
            self.save()
            self.create_comment(**kwargs)
        return is_done, msg

    def draft(self, **kwargs):
        stock = self.get_stock()
        if self.state == 'confirm':
            is_done, msg = stock.reserve_stock(unlock=True)
            if is_done:
                self.state = 'draft'
                self.save()
                self.create_comment(**kwargs)
            return is_done, msg
        return False, ''

    def cancel(self, **kwargs):
        is_done, msg = True, ''
        if self.state == 'confirm':
            stock = self.get_stock()
            is_done, msg = stock.reserve_stock(unlock=True)
            if is_done:
                self.state = 'cancel'
                self.save()
                self.create_comment(**kwargs)
        elif self.state == 'done':
            self.state = 'cancel'
            self.save()
            self.create_comment(**kwargs)
        elif self.state == 'draft':
            self.state = 'cancel'
            self.save()
            self.create_comment(**kwargs)
        for invoice in self.invoices.all():
            invoice.state = 'cancel'
            invoice.save()
            comment = '更新 %s <a href="%s">%s</a>状态:%s, 修改本账单' % (
                self._meta.verbose_name, self.get_absolute_url(), self, self.state)
            invoice.create_comment(**{'comment': comment})
        return is_done, msg

    def make_expenses_invoice(self):
        from partner.models import Partner
        from invoice.models import Account, CreateInvoice
        if self.get_expenses_amount() > 0:
            items_dict = {}
            for item in self.items.all():
                items_dict.update(item.prepare_expenses_invoice_item())
            if items_dict:
                partner = Partner.get_expenses_partner() if not self.partner else self.partner
                return CreateInvoice(self, partner, items_dict, usage='运输费',
                                     state='confirm')


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

    expenses = GenericRelation('mrp.Expenses')

    class Meta:
        verbose_name = '移库单明细行'

    def get_location(self):
        loc = self.location if self.location else self.order.location
        return loc

    def get_location_dest(self):
        dest = self.location_dest if self.location_dest else self.order.location_dest
        return dest

    def prepare_expenses_invoice_item(self):

        if not self.expenses.all():
            item = '{}({}=>{})'.format(str(self.product), self.location,
                                       self.location_dest)
            return {item: {'item': item, 'from_order_item': self, 'line': self.line, 'quantity': 0, 'price': 0,
                           'uom': self.product.get_uom()}}

        items = {}
        for expense in self.expenses.all():
            item = '{} {}({}=>{})'.format(expense.expense.name, str(self.product), self.location,
                                          self.location_dest)
            items.update(
                {item: {'item': item, 'from_order_item': self, 'quantity': expense.quantity, 'price': expense.price,
                        'uom': expense.uom}})
        return items

    def get_expenses_amount(self):
        return sum(expense.amount for expense in self.expenses.all())
