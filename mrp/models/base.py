from decimal import Decimal
from django.contrib.contenttypes.fields import GenericRelation, GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse

from public.fields import LineField
from purchase.models import OrderAbstract

UOM_CHOICES = (('t', '吨'), ('m3', '立方'), ('m2', '平方'))
EXPENSES_UOM = (('part', '夹数'), ('quantity', '数量(t/m3/m2)'), ('one', '次/个/车'))


class MrpOrderAbstract(OrderAbstract):
    location = models.ForeignKey('stock.Location', on_delete=models.SET_NULL, related_name='%(class)s_location',
                                 verbose_name='原库位', null=True, blank=True)
    location_dest = models.ForeignKey('stock.Location', on_delete=models.SET_NULL,
                                      related_name='%(class)s_location_dest',
                                      verbose_name='目标库位', null=True, blank=True)
    stock_trace = GenericRelation('stock.StockTrace')
    warehouse = models.ForeignKey('stock.Warehouse', on_delete=models.CASCADE, verbose_name='仓库')
    date = models.DateField('日期')
    created = models.DateField('创建日期', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        abstract = True

    def get_location(self):
        raise ValueError('没有设置get_location')

    def get_location_dest(self):
        raise ValueError('没有设置get_location_dest')

    def save(self, *args, **kwargs):
        self.location = self.get_location()
        self.location_dest = self.get_location_dest()
        super(MrpOrderAbstract, self).save(*args, **kwargs)

    def __str__(self):
        return self.order


class OrderItemBase(models.Model):
    line = LineField(for_fields=['order'], blank=True, verbose_name='行')
    location = models.ForeignKey('stock.Location', related_name='%(class)s_location', verbose_name='库位',
                                 on_delete=models.DO_NOTHING, blank=True, null=True)
    location_dest = models.ForeignKey('stock.Location', related_name='%(class)s_location_dest', verbose_name='目标库位',
                                      on_delete=models.DO_NOTHING, blank=True, null=True)
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE, verbose_name='product')
    piece = models.IntegerField('件', default=1)
    quantity = models.DecimalField('数量', decimal_places=2, max_digits=10)
    uom = models.CharField('计量单位', null=False, choices=UOM_CHOICES, max_length=10, default='t')

    class Meta:
        abstract = True

    def get_location(self):
        return self.order.location

    def get_location_dest(self):
        return self.order.location_dest

    def save(self, *args, **kwargs):
        self.location = self.get_location()
        self.location_dest = self.get_location_dest()
        super(OrderItemBase, self).save(*args, **kwargs)


class Expenses(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey()
    expense = models.ForeignKey('ExpensesItem', on_delete=models.CASCADE, verbose_name='费用名称')
    expense_by_uom = models.CharField('计费单位', choices=EXPENSES_UOM, max_length=20)

    class Meta:
        verbose_name = '费用明细'

    def get_quantity(self):
        obj = self.content_type.model_class().objects.get(pk=self.object_id)
        if self.expense_by_uom == 'part':
            quantity = None if not obj.package_list else obj.package_list.get_part()
        elif self.expense_by_uom == 'quantity':
            quantity = obj.quantity
        else:
            quantity = 1
        quantity = 0 if not quantity else quantity
        return quantity

    def get_uom(self):
        obj = self.content_type.model_class().objects.get(pk=self.object_id)
        if self.expense_by_uom == 'part':
            uom = '夹'
        elif self.expense_by_uom == 'quantity':
            uom = obj.uom
        else:
            return self.expense.uom_name
        return uom

    @property
    def amount(self):
        return Decimal('{0:.2f}'.format(self.get_quantity() * self.expense.price))

    def __str__(self):
        return '{}: {}*{}/{}'.format(self.expense.name, self.get_quantity(), self.expense.price, self.get_uom())


class ExpensesItem(models.Model):
    name = models.CharField('费用名称', max_length=20)
    price = models.DecimalField('单价', max_digits=8, decimal_places=2)
    uom_name = models.CharField('单位', max_length=10)

    class Meta:
        verbose_name = '费用名称'

    def __str__(self):
        return '{}:{}/{}'.format(self.name, self.price, self.uom_name)

    def get_update_url(self):
        return reverse('expenses_item_update', args=[self.id])
