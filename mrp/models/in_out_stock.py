from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.db import models
from django.urls import reverse

from invoice.models import CreateInvoice
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

    @property
    def from_order(self):
        return self.sales_order or self.purchase_order

    def __str__(self):
        return self.full_order

    @property
    def full_order(self):
        from_order = self.purchase_order or self.sales_order
        count = from_order.in_out_order.filter(state__in=('confirm', 'done')).count()
        if count > 1:
            last_display = '({})'.format(count)
        else:
            last_display = ''
        return '{}/{}{}'.format(from_order, self.get_type_display(), last_display)

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

    def done(self):
        stock = self.get_stock()
        if self.sales_order:
            unlock, unlock_msg = stock.reserve_stock(unlock=True)
            if unlock:
                is_done, msg = stock.handle_stock()
                if is_done:
                    self.state = 'done'
                    self.save()
                else:
                    stock.reserve_stock()
                    return is_done, msg
            return unlock, unlock_msg
        else:
            is_done, msg = stock.handle_stock()
            if is_done:
                self.state = 'done'
                self.save()
            return is_done, msg

    def cancel(self):
        stock = self.get_stock()
        if self.sales_order.state == 'confirm':
            is_done, msg = stock.reserve_stock()
            if is_done:
                self.invoices.all().update(state='cancel')
                self.state = 'cancel'
                self.save()
            return is_done, msg

    @property
    def has_from_order_invoice(self):
        if self.invoices.all():
            for invoice in self.invoices.all():
                if invoice.usage == '货款':
                    return True
        return False

    def make_from_order_invoice(self):
        items_dict_lst = [item.prepare_from_order_invoice_item() for item in self.items.all()]
        return CreateInvoice(self, self.from_order.partner, items_dict_lst, usage='货款', type=1).invoice

    def make_invoice(self):
        lst = [item.prepare_invoice_item() for item in self.items.all()]
        if lst:
            items_dict_lst = unpack_lst(lst)
            return CreateInvoice(self, self.partner.get_expenses_partner(), items_dict_lst, usage='杂费', state='done')


class InOutOrderItem(OrderItemBase):
    order = models.ForeignKey('InOutOrder', on_delete=models.CASCADE, related_name='items', verbose_name='对应订单')
    package_list = models.ForeignKey('product.PackageList', on_delete=models.SET_NULL, blank=True, null=True,
                                     verbose_name='码单')
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

    def prepare_from_order_invoice_item(self):
        return {'item': str(self.product), 'quantity': self.quantity, 'uom': self.uom,
                'price': self.get_from_order_item().price,
                'sales_order_item': self.get_from_order_item()}

    def prepare_invoice_item(self):
        return [{'item': '{}:{}'.format(str(self.product), expense.name), 'quantity': expense.quantity,
                 'price': expense.price,
                 'uom': expense.uom} for expense in self.expenses.all()]
