import collections

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.db import models
from django.db.models import Q
from django.urls import reverse

from invoice.models import CreateInvoice, Account
from mrp.models import MrpOrderAbstract, OrderItemBase
from public.fields import OrderField
from public.stock_operate import StockOperate

UOM_CHOICES = (('t', '吨'), ('m3', '立方'), ('m2', '平方'))
OPERATION_TYPE = (('in', '入库'), ('out', '出库'))


def unpack_lst(lst):
    ls = []
    for l in lst:
        if isinstance(l, list):
            ls.extend(unpack_lst(l))
        else:
            if l:
                ls.append(l)
    return ls


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

    def _get_invoice_usage(self):
        return '杂费'

    @property
    def from_order(self):
        return self.sales_order or self.purchase_order

    def __str__(self):
        return '[{}]{}'.format(self.get_type_display(), self.order)

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

    def get_products_amount(self):
        return sum(item.quantity * item.get_from_order_item().price for item in self.items.all())

    def get_stock(self):
        return StockOperate(self, self.items.all())

    def get_expenses_amount(self):
        return sum(item.get_expenses_amount() for item in self.items.all())

    def done(self, **kwargs):
        stock = self.get_stock()
        if self.sales_order:
            # 如果是对应的是销售订单
            unlock, unlock_msg = stock.reserve_stock(unlock=True)
            # 如果解库成功就操作库存移动
            # 否则就把不能解库的状态及msg返回
            if unlock:
                is_done, msg = stock.handle_stock()
                # 如果库存移动成功就更改状态并create comment
                # 否则就把不能库存移动的状态及msg返回
                if is_done:
                    self.make_invoice()
                    self.state = 'done'
                    self.save()
                    self.create_comment(**kwargs)
                    comment = '完成 %s :<a href="%s">%s</a>' % (self._meta.verbose_name,
                                                              self.get_absolute_url(), self,)
                    self.from_order.done(**{'comment': comment})
                else:
                    stock.reserve_stock()
                    return is_done, msg
            return unlock, unlock_msg
        else:
            # 如果是对应的是采购订单
            is_done, msg = stock.handle_stock()
            if is_done:
                # 如果库存移动成功就更改状态及create comment
                self.make_invoice()
                self.state = 'done'
                self.save()
                self.create_comment(**kwargs)
                comment = '完成 %s :<a href="%s">%s</a>' % (self._meta.verbose_name,
                                                          self.get_absolute_url(), self)

                self.from_order.done(**{'comment': comment})
            return is_done, msg

    def cancel(self, **kwargs):
        stock = self.get_stock()
        if self.sales_order.state == 'confirm':
            is_done, msg = stock.reserve_stock()
            if is_done:
                self.state = 'cancel'
                self.save()
                self.create_comment(**kwargs)
                comment = '更改 %s <a href="%s">%s</a>状态:%s, 取消本账单' % (
                    self._meta.verbose_name, self.get_absolute_url(), self, self.state)
                for invoice in self.invoices.all():
                    invoice.cancel(**{'comment': comment})
            return is_done, msg

    @property
    def has_from_order_invoice(self):
        if self.invoices.all():
            from_order_items_ids = {item.get_from_order_item() for item in self.items.all()}
            for invoice in self.invoices.all():
                for item in invoice.items.all():
                    if item.from_order_item in from_order_items_ids:
                        return True
        return False

    def make_from_order_invoice(self):
        type = -1 if self.type == 'in' else 1
        items_dict = {}
        state = self.state if self.state != 'done' else 'confirm'
        for item in self.items.all():
            items_dict.update(item.prepare_from_order_invoice_item())
        return CreateInvoice(self.from_order, self.from_order.partner, items_dict, usage='货款', type=type,
                             state=state).invoice

    def make_invoice(self):
        from partner.models import Partner
        lst = unpack_lst(item.prepare_expenses_invoice_item() for item in self.items.all())
        if lst:
            items_dict = {}
            for dt in lst:
                items_dict[dt['item']] = dt
            payment = {'partner': Partner.get_expenses_partner(),
                       'account': Account.get_expense_account()}
            return CreateInvoice(self, Partner.get_expenses_partner(), items_dict, usage='杂费',
                                 state='confirm', payment=payment)


class InOutOrderItem(OrderItemBase):
    order = models.ForeignKey('InOutOrder', on_delete=models.CASCADE, related_name='items', verbose_name='对应订单')

    sales_order_item = models.ForeignKey('sales.SalesOrderItem', on_delete=models.CASCADE,
                                         related_name='in_out_order_items', blank=True, null=True,
                                         verbose_name='销售订单明细行')
    purchase_order_item = models.ForeignKey('purchase.PurchaseOrderItem', on_delete=models.CASCADE,
                                            related_name='in_out_order_items', blank=True, null=True,
                                            verbose_name='采购订单明细行')
    expenses = GenericRelation('mrp.Expenses')

    class Meta:
        verbose_name = '出入库操作明细行'

    def save(self, *args, **kwargs):
        if self.package_list:
            self.piece = self.package_list.get_piece()
            self.quantity = self.package_list.get_quantity()
        super().save(*args, **kwargs)

    def get_from_order_item(self):
        return self.sales_order_item or self.purchase_order_item

    def get_can_make_from_order_invoice_qty(self):
        return self.get_from_order_item().get_can_make_invoice_qty()

    def prepare_from_order_invoice_item(self):
        return {str(self.product): {'line': self.line, 'item': str(self.product),
                                    'quantity': self.quantity,
                                    'uom': self.uom,
                                    'price': self.get_from_order_item().price,
                                    'from_order_item': self.get_from_order_item()}}

    def prepare_expenses_invoice_item(self):
        return [{'item': '{}:{}'.format(str(self.product), expense.expense.name), 'from_order_item': self,
                 'line': self.line,
                 'quantity': expense.quantity, 'price': expense.price,
                 'uom': expense.uom} for expense in self.expenses.all()]

    def get_expenses_amount(self):
        return sum(expense.amount for expense in self.expenses.all())
