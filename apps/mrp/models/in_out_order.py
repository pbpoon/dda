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
        ordering = ('-date', '-created')

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
        pieces = 0
        for item in self.items.all():
            pieces += item.piece

        if self.sales_order:
            # 如果是对应的是销售订单
            unlock, unlock_msg = stock.reserve_stock(unlock=True)
            # 如果解库成功就操作库存移动
            # 否则就把不能解库的状态及msg返回
            print('unlock=%s,msg=%s' % (unlock, unlock_msg))
            if unlock:
                is_done, msg = stock.handle_stock()
                # 如果库存移动成功就更改状态并create comment
                # 否则就把不能库存移动的状态及msg返回
                print('handle_stock=%s,msg=%s' % (is_done, msg))
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

    def make_purchase_order_items(self):
        # 如果是新建状态
        # 该采购单已收货的items取出
        already_check_in_items = self.purchase_order.items.filter(
            order__in_out_order__state__in=('confirm', 'done'))
        purchase_order_items = self.purchase_order.items.all()
        if already_check_in_items:
            purchase_order_items.exclude(product_id__in=[item.product.id for item in already_check_in_items])
        for item in purchase_order_items:
            InOutOrderItem.objects.create(product=item.product, piece=item.piece,
                                          quantity=item.quantity,
                                          uom=item.uom, order=self, purchase_order_item=item)

    def make_sales_order_items(self):
        # 选出产品类型为荒料的已出货项的
        from_order_items = self.sales_order.items.all()
        for item in from_order_items:
            if item.get_can_in_out_order_qty()['piece'] > 0:
                stock = item.product.stock.filter(
                    location_id__in=self.warehouse.get_main_location().get_child_list(),
                    product=item.product).distinct()
                if not stock:
                    continue
                if item.package_list:
                    package = item.package_list.make_package_from_list(item.product_id,
                                                                       from_package_list=item.package_list)
                else:
                    package = None

                defaults = {'piece': stock[0].piece,
                            'quantity': stock[0].quantity,
                            'package_list': package, 'product': item.product, 'order': self,
                            'uom': item.uom, 'sales_order_item': item}
                InOutOrderItem.objects.create(**defaults)

    def make_items(self):
        # 如果是update状态，有object就返回items
        if self.purchase_order:
            return self.make_purchase_order_items()
        return self.make_sales_order_items()

    def save(self, *args, **kwargs):
        new = False
        if not self.pk:
            new = True
        super().save(*args, **kwargs)
        if new:
            self.make_items()


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

        # already_check_out_items = self.order.sales_order.items.filter(
        #     order__in_out_order__state__in=('confirm', 'done'), product__type='block')
        # sales_order_items = self.order.sales_order.items.all()
        # if already_check_out_items:
        #     sales_order_items.exclude(product_id__in=[item.product.id for item in already_check_out_items])
        # if sales_order_items:
        #     # 生成新item的项目
        #     for item in sales_order_items:
        #         package = None
        #         if item.product.type == 'slab':
        #             # slabs_id_lst = [item.get_slab_id() for item in
        #             #                 item.package_list.items.filter(slab__stock__isnull=False,
        #             #                                                slab__stock__location=self.object.warehouse.get_main_location())]
        #             # 如果有码单，就生成一张新码单，并把码单的from_package_list链接到旧的码单，
        #             # 为了在提货单draft状态下可以选择到旧码单的slab
        #             # ps：后来更改为建一张空码单， 提货时候再选择
        #             package = item.package_list.make_package_from_list(item.product_id,
        #                                                                from_package_list=item.package_list)
        #         defaults = {'piece': item.piece if not package else package.get_piece(),
        #                     'quantity': item.quantity if not package else package.get_quantity(),
        #                     'package_list': package, 'product': item.product, 'order': self.object,
        #                     'uom': item.uom, 'sales_order_item': item}
        #         InOutOrderItem.objects.create(**defaults)
        # return self.object.items.all()
