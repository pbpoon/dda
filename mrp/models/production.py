import collections
import math

from django.contrib.contenttypes.fields import GenericRelation
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import decimal
from django.db import models
from django.urls import reverse

from invoice.models import CreateInvoice
from mrp.models import MrpOrderAbstract, OrderItemBase
from product.models import Product
from public.fields import OrderField
# from stock.stock_operate import StockOperate
from public.stock_operate import StockOperate

UOM_CHOICES = (('t', '吨'), ('m3', '立方'), ('m2', '平方'))
TYPE_CHOICES = (('block', '荒料'), ('semi_slab', '毛板'), ('slab', '板材'))
EXPENSE_BY_CHOICES = (('raw', '原材料项'), ('produce', '产品项'), ('all', '原料及产品'))


class ProductionType(models.Model):
    name = models.CharField('业务类型', max_length=30)
    expense_by = models.CharField('费用结算按', max_length=10, choices=EXPENSE_BY_CHOICES)
    raw_item_type = models.CharField('原材料类型', max_length=10, choices=TYPE_CHOICES, default='block')
    produce_item_type = models.CharField('产出品类型', max_length=10, choices=TYPE_CHOICES, default='block')
    activate = models.BooleanField('启用', default=True)

    class Meta:
        verbose_name = '生产业务类型明细'

    def get_absolute_url(self):
        return reverse('production_type_detail', args=[self.id])

    def get_update_url(self):
        return reverse('production_type_update', args=[self.id])

    def __str__(self):
        return self.name


class ProductionOrder(MrpOrderAbstract):
    order = OrderField(order_str='MO', blank=True, verbose_name='单号', default='New', max_length=20)
    production_type = models.ForeignKey(ProductionType, on_delete=models.CASCADE, verbose_name='业务类型',
                                        limit_choices_to={'activate': True})
    partner = models.ForeignKey('partner.Partner', on_delete=models.CASCADE,
                                verbose_name='生产单位', limit_choices_to={'type': 'production'})

    class Meta:
        verbose_name = '生产订单'
        ordering = ('-date',)

    def _get_invoice_usage(self):
        return '%s费用' % self.production_type.name

    def get_absolute_url(self):
        return reverse('production_detail', args=[self.id])

    def get_update_url(self):
        return reverse('production_update', args=[self.id])

    def get_create_item_url(self):
        return reverse('production_raw_item_create', args=[self.id])

    def get_location(self):
        return self.warehouse.get_main_location()

    def get_location_dest(self):
        return self.warehouse.get_production_location()

    def get_total(self):
        """
        template使用方式
        {% for key, item in object.get_total.items %}
        {{ key }}:{% if item.part %}{{ item.part }}夹 / {% endif %}{{ item.piece }}件 / {{ item.quantity }}{{ item.uom }}<br>
        {% endfor %}
        """
        total = {}
        for item in self.get_all_items():
            if not item.product:
                continue
            d = collections.defaultdict(lambda: 0)
            a = total.setdefault(item.product.get_type_display(), d)
            a['piece'] += item.piece
            a['quantity'] += item.quantity
            d['part'] += item.package_list.get_part() if item.package_list else 0
            a['uom'] = item.uom
            # total.setdefault(item.product.get_type_display(), {}).update(d)
        return total

    def get_stock(self):
        items = list(self.items.all())
        items.extend(list(self.produce_items.all()))
        return StockOperate(order=self, items=items)

    def get_invoices(self):
        invoices = set(self.invoices.all())
        invoices |= {invoice.order for item in self.items.all() for invoice in item.invoice_items.all().distinct()}
        return invoices

    def done(self, **kwargs):
        is_done, msg = self.get_stock().handle_stock()
        if is_done:
            self.state = 'done'
            self.save()
            self.create_comment(**kwargs)
            self.make_invoice()
            self.make_expenses_invoice()
        return is_done, msg

    def cancel(self, **kwargs):
        self.state = 'cancel'
        self.save()
        self.create_comment(**kwargs)
        for invoice in self.get_invoices():
            invoice.state = 'cancel'
            invoice.save()
            comment = '更新 %s <a href="%s">%s</a>状态:%s, 修改本账单' % (
                self._meta.verbose_name, self.get_absolute_url(), self, self.state)
            invoice.create_comment(**{'comment': comment})
        return True, ''

    def get_all_items(self):
        items = list(self.items.all())
        items.extend(list(self.produce_items.all()))
        return items

    def get_make_invoice_items(self):
        if self.production_type.expense_by == 'raw':
            return self.items.all()
        elif self.production_type.expense_by == 'produce':
            return self.produce_items.all()
        else:
            return self.get_all_items()

    def make_invoice(self):
        items = self.get_make_invoice_items()
        items_dict = {}
        for item in items:
            items_dict.update(item.prepare_invoice_item())
        state = self.state if self.state != 'done' else 'confirm'
        return CreateInvoice(self, self.partner, items_dict, type=-1, state=state).invoice

    def get_expenses_amount(self):
        return sum(item.get_expenses_amount() for item in self.get_all_items())

    def make_expenses_invoice(self):
        from partner.models import Partner
        from invoice.models import Account, CreateInvoice
        if self.get_expenses_amount() > 0:
            items_dict = {}
            for item in self.get_all_items():
                items_dict.update(item.prepare_invoice_item())
            if items_dict:
                partner = Partner.get_expenses_partner() if not self.partner else self.partner
                return CreateInvoice(self, partner, items_dict, usage='杂费',
                                     state='confirm', type=-1)


class ProductionOrderRawItem(OrderItemBase):
    order = models.ForeignKey('ProductionOrder', on_delete=models.CASCADE, related_name='items')
    piece = models.IntegerField('件', default=1, blank=True, null=True)
    quantity = models.DecimalField('数量', max_digits=5, decimal_places=2, null=True, blank=True)
    uom = models.CharField('计量单位', null=False, choices=UOM_CHOICES, max_length=10, default='t')
    price = models.DecimalField('单价', max_digits=8, decimal_places=2, blank=True, null=True)

    class Meta:
        verbose_name = '生产单原料行'

    @property
    def amount(self):
        return self.get_amount()

    def get_amount(self):
        if self.product.type == 'block':
            return self.get_m3() * self.price
        return 0

    def get_m3(self):
        return self.product.get_m3()

    def __str__(self):
        return str(self.product)

    def get_expenses_amount(self):
        return sum(expense.amount for expense in self.expenses.all())

    def prepare_expenses_invoice_item(self):
        return [{'item': '{}:{}'.format(str(self.product), expense.expense.name), 'from_order_item': self,
                 'line': self.line,
                 'quantity': expense.quantity, 'price': expense.price,
                 'uom': expense.uom} for expense in self.expenses.all()]

    def prepare_invoice_item(self):
        return {'%s:%s费' % (str(self.product), self.order.production_type): {
            'item': '%s:%s费' % (str(self.product), self.order.production_type),
            'from_order_item': self,
            'quantity': self.quantity,
            'line': self.line,
            'price': self.price}}

    # 估算毛板的出材率
    def semi_slab_single_qty(self):
        # 先取出对应的item的最小的厚度
        all_produces = self.produces.all()
        if not all_produces:
            return None
        all_produces_dict = {i.thickness: i.piece for i in all_produces}
        min_thickness = min_thickness_key = min(all_produces_dict.keys())
        # 把最小如果是1。5的就改成1。4，之后把厚度+0。43刀头的厚度
        min_thickness = decimal.Decimal(1.4) if min_thickness == 1.5 else min_thickness
        min_thickness += decimal.Decimal(0.43)
        # 用m3 x 厚度出材率计算出最小规格的总出材率
        m3 = self.product.get_m3()
        total_min_thickness_m2 = m3 * (decimal.Decimal(100) - min_thickness) / min_thickness
        total_min_piece = all_produces_dict[min_thickness_key]
        # 如果该荒料的规格厚度为多个，就用其他厚度x件数就算出该厚度为最小厚度的件数，
        # 用最小厚度添加计算出来的件数，最总计算出如果该料界最小厚度会有多少件数，最后用最小厚度的总估算平方数除以估算的总件，计算出单价平方数
        if len(all_produces) > 1:
            for i in all_produces:
                total_min_piece += math.ceil((i.thickness + decimal.Decimal(0.43) * i.piece / min_thickness))
        single_qty = total_min_thickness_m2 / total_min_piece
        return single_qty

    def update_produces_quantity(self):
        single_qty = self.semi_slab_single_qty()
        if single_qty:
            for p in self.produces.all():
                ProductionOrderProduceItem.objects.filter(pk=p.id).update(quantity=p.piece * single_qty)
                Product.objects.filter(pk=p.product.id).update(semi_slab_single_qty=single_qty)


class ProductionOrderProduceItem(OrderItemBase):
    order = models.ForeignKey('ProductionOrder', on_delete=models.CASCADE, related_name='produce_items',
                              verbose_name='对应生产单')
    raw_item = models.ForeignKey('ProductionOrderRawItem', on_delete=models.CASCADE, related_name='produces',

                                 verbose_name='原材料')
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE, verbose_name='product', blank=True,
                                null=True)
    thickness = models.DecimalField('厚度规格', max_digits=5, decimal_places=2, blank=True, null=True)
    quantity = models.DecimalField('数量', decimal_places=2, max_digits=10, null=True, blank=True)
    price = models.DecimalField('单价', max_digits=8, decimal_places=2, null=True, blank=True)
    draft_package_list = models.ForeignKey('product.DraftPackageList', on_delete=models.SET_NULL, blank=True, null=True,
                                           verbose_name='草稿码单')
    package_list = models.ForeignKey('product.PackageList', on_delete=models.SET_NULL, blank=True, null=True,
                                     verbose_name='码单')

    class Meta:
        verbose_name = '生产单成品行'
        # unique_together = ['thickness', 'raw_item']

    @property
    def amount(self):
        return self.get_amount()

    def get_amount(self):
        if self.product.type == 'slab':
            return self.quantity * self.price
        return 0

    def get_location(self):
        return self.order.location_dest

    def get_location_dest(self):
        return self.order.location

    # def save(self, *args, **kwargs):
    # self.order = self.raw_item.order
    # thickness = self.thickness or self.raw_item.product.thickness
    # self.product = self.raw_item.product.create_product(type=self.order.production_type.produce_item_type,
    #                                                     thickness=thickness)
    # if self.draft_package_list:
    #     self.package_list = self.draft_package_list.make_package_list(product=self.product)
    #     self.piece = self.package_list.get_piece()
    #     self.quantity = self.package_list.get_quantity()
    #     self.draft_package_list = None
    # self.uom = self.product.get_uom()
    # super().save(*args, **kwargs)

    def get_expenses_amount(self):
        return sum(expense.amount for expense in self.expenses.all())

    def prepare_invoice_item(self):
        return {'%s:%s费' % (str(self.product), self.order.production_type): {
            'item': '%s:%s费' % (str(self.product), self.order.production_type),
            'from_order_item': self,
            'quantity': self.quantity,
            'line': self.line,
            'price': self.price}}

    def prepare_expenses_invoice_item(self):
        return [{'item': '{}:{}'.format(str(self.product), expense.expense.name), 'from_order_item': self,
                 'line': self.line,
                 'quantity': expense.quantity, 'price': expense.price,
                 'uom': expense.uom} for expense in self.expenses.all()]


# 更新毛板平方数的
@receiver(post_save, sender=ProductionOrderProduceItem, dispatch_uid='dis')
def production_produce_item_post_save_update_produces_quantity(sender, **kwargs):
    instance = kwargs['instance']
    type = instance.order.production_type.produce_item_type
    if type == 'semi_slab':
        instance.raw_item.update_produces_quantity()
    elif type == 'slab':
        package_list = instance.package_list
        if package_list:
            instance.raw_item.piece = package_list.get_piece()
            instance.raw_item.quantity = package_list.get_quantity()
            instance.raw_item.save()


@receiver(post_delete, sender=ProductionOrderProduceItem, dispatch_uid='sid')
def production_produce_item_post_delete_update_produces_quantity(sender, **kwargs):
    instance = kwargs['instance']
    type = instance.order.production_type.produce_item_type
    if type == 'semi_slab':
        instance.raw_item.update_produces_quantity()
    elif type == 'slab':
        package_list = instance.package_list
        if package_list:
            instance.raw_item.piece = None
            instance.raw_item.quantity = None
            instance.raw_item.save()
