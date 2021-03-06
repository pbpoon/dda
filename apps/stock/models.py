from collections import Counter

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db.models import Q
from django.urls import reverse
from django.contrib import messages

UOM_CHOICES = (('t', '吨'), ('m3', '立方'))

USAGE_CHOICES = (('supplier', '供应商库位'), ('customer', '客户库位'),
                 ('production', '生产库位'), ('internal', '存货库位'),
                 ('inventory', '盘点库位'))


def tree_view(obj):
    result = []
    for c in obj.child.all():
        result.append(c)
        if len(c.child.all()) > 0:
            result.append(tree_view(c))
    return result


class Warehouse(models.Model):
    """
    当创建一个warehouse时候，相应的创建一个内部的库位，为置顶库位
    """
    name = models.CharField('仓库名称', max_length=50, unique=True, db_index=True)
    code = models.CharField('缩写名称', max_length=20, blank=True, null=True)
    is_activate = models.BooleanField('启用', default=True)
    partner = models.ForeignKey('partner.Partner', on_delete=models.SET_NULL, verbose_name='合作伙伴', null=True,
                                blank=True, related_name='warehouse',
                                limit_choices_to={'type__in': ('production', 'supplier')})
    created = models.DateTimeField('创建时间', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)
    is_production = models.BooleanField('有生产活动', default=False)
    _address = models.TextField('地址', blank=True, null=True)

    class Meta:
        verbose_name = '仓库信息'

    def __str__(self):
        return '{}@{}'.format(self.partner if self.partner else '', self.name)

    @property
    def address(self):
        return self._address or self.__str__()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.locations.filter(is_main=True):
            Location.objects.create(warehouse_id=self.id, name='仓库', is_main=True, usage='internal')
        if self.is_production:
            Location.objects.get_or_create(warehouse_id=self.id, is_virtual=True, usage='production', name='生产库位')

    def get_absolute_url(self):
        return reverse('warehouse_detail', args=[self.id])

    def get_main_location(self):
        return self.locations.get(is_main=True, warehouse_id=self.id)

    def get_production_location(self):
        loc, _ = Location.objects.get_or_create(warehouse=self, name='production', usage='production', is_virtual=True)
        return loc

    def get_update_url(self):
        return reverse('warehouse_update', args=[self.id])

    def get_create_item_url(self):
        return reverse('location_create', args=[self.id])


class Location(models.Model):
    """
    如果is_virtual=True,就不能有子库位
    """
    warehouse = models.ForeignKey('Warehouse', related_name='locations', on_delete=models.SET_NULL, verbose_name='所属仓库',
                                  blank=True, null=True)
    name = models.CharField('库位名称', max_length=50)
    parent = models.ForeignKey('self', related_name='child', null=True, blank=True, verbose_name='上级库位',
                               on_delete=models.CASCADE, limit_choices_to={'is_virtual': False, 'is_activate': True})
    is_main = models.BooleanField('主库位', default=False, help_text='主库位，只有在创建warehouse时一并创建')
    usage = models.CharField('库位用途', choices=USAGE_CHOICES, null=False, max_length=50)
    is_virtual = models.BooleanField('虚拟库位', default=False)
    desc = models.TextField('描述', blank=True, null=True)
    is_activate = models.BooleanField('启用', default=True)
    created = models.DateTimeField('创建时间', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '库位信息'
        unique_together = ['warehouse', 'name']

    def get_full_name(self):
        name = self.name
        parent = self.parent
        while parent:
            name = '{}/{}'.format(parent.name, name)
            parent = parent.parent
        warehouse_name = self.warehouse.name + '/' if self.warehouse else ''
        string = '%s%s' % (warehouse_name, name)
        if self.is_main:
            string += '**'
        return string

    def __str__(self):
        return self.get_full_name()

    def get_absolute_url(self):
        return reverse('location_detail', args=[self.id])

    def get_main_location(self):
        if self.is_main:
            return self
        parent = self.parent
        while parent:
            if parent.is_main:
                return parent
            parent = parent.parent
        return parent

    @staticmethod
    def get_inventory_location():
        loc, _ = Location.objects.get_or_create(usage='inventory', name='盘点库位', is_virtual=True)
        return loc

    def get_child_list(self, container=None):
        if container is None:
            container = [self.id]
        result = container
        for chl in self.child.all():
            result.append(chl.id)
            if chl.child.count() > 0:
                chl.get_child_list(result)
        return result

    def get_child(self):
        return self.__class__.objects.filter(id__in=self.get_child_list()).distinct()

    def tree_view(self, container=None):
        if container is None:
            container = []
        result = container
        for chl in self.child.all():
            result.append(chl)
            if chl.child.count() > 0:
                chl.tree_view(result)
        return (self, result)


class StockTrace(models.Model):
    """
    只在记录什么单的product操作了什么，用作链式记账
    """
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='order_stock_trace')
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey()
    location = models.ForeignKey('Location', related_name='stock_trace_from', verbose_name='库位',
                                 on_delete=models.DO_NOTHING)
    location_dest = models.ForeignKey('Location', related_name='stock_trace_to', verbose_name='目标库位',
                                      on_delete=models.DO_NOTHING)
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE, related_name='product_stock_trace')
    created = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '库存轨迹'

    def __str__(self):
        return '{}|{}:{}=>{}'.format(self.get_obj().order, self.product, self.location, self.location_dest)

    def get_obj(self):
        return self.content_type.model_class().objects.get(pk=self.object_id)


class OriginalStockTrace(models.Model):
    block = models.ForeignKey('product.Block', on_delete=models.SET_NULL, blank=True, null=True, verbose_name='编号',
                              related_name='original_stock_trace')
    address = models.CharField('仓库', max_length=20)
    date = models.DateField('日期')
    part = models.SmallIntegerField('夹', blank=True, null=True)
    piece = models.SmallIntegerField('件', blank=True, null=True)
    quantity = models.DecimalField('数量', decimal_places=2, max_digits=10)
    uom = models.CharField('单位', max_length=10)
    stock_trace = models.CharField('事务', max_length=10)

    class Meta:
        verbose_name = '旧数据库存事务'
        ordering = ('-date',)


class Stock(models.Model):
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE, related_name='stock', db_index=True)
    piece = models.IntegerField('件', default=1)
    quantity = models.DecimalField('数量', decimal_places=2, max_digits=10)
    reserve_quantity = models.DecimalField('预留数量', decimal_places=2, max_digits=10, default=0)
    reserve_piece = models.IntegerField('预留件', default=0)
    uom = models.CharField('单位', choices=UOM_CHOICES, max_length=6)
    location = models.ForeignKey('Location', on_delete=models.CASCADE, limit_choices_to={'is_virtual': False},
                                 related_name='stock', db_index=True)
    created = models.DateTimeField('创建时间', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)
    main_long = models.SmallIntegerField('长', blank=True, null=True)
    main_height = models.SmallIntegerField('高', blank=True, null=True)
    main_width = models.SmallIntegerField('宽', blank=True, null=True)

    class Meta:
        verbose_name = '库存'
        unique_together = ('product', 'location')

    def get_quantity(self, number=None):
        qs = self.items.all()
        if number:
            qs = self.items.filter(part_number=number)
        return sum(item.get_quantity() for item in qs)

    def get_part(self):
        return len({item.part_number for item in self.items.all()})

    def get_piece(self, number=None):
        qs = self.items.all()
        if number:
            qs = qs.filter(part_number=number)
        return qs.count()

    def get_part_number(self):
        return {item.part_number for item in self.items.all()}

    def get_weight(self, number=None):
        qs = self.items.all()
        if number:
            qs = qs.filter(part_number=number)
        return '约 {:.2f}t'.format(sum(item.get_weight() for item in qs))

    # def get_main_size(self):
    #

    def __str__(self):
        return "{}@{}:{}件/{}{}".format(self.product, self.location, self.piece, self.quantity, self.uom)

    def get_absolute_url(self):
        return reverse('stock_detail', args=[self.id])

    @staticmethod
    def _get_stock(product, location=None, slabs=None, check_in=False):
        # 取得库存的记录
        kwargs = {'product_id': product.id}
        if location:
            if check_in:
                kwargs['location_id'] = location.id
                return Stock.objects.filter(**kwargs)
            location_id_list = location.get_child_list()
            kwargs['location_id__in'] = location_id_list
        qs = Stock.objects.filter(**kwargs).distinct()
        if slabs:
            qs = qs.filter(items__in=[s.id for s in slabs]).distinct()
        return qs

    @staticmethod
    def get_available(product, location=None, slabs=None):
        """
        Args:
            product: object产品
            location: object库位
            slabs: questset板材

        Returns:元祖，（件，数量）

        """
        available_stock = Stock._get_stock(product=product, location=location, slabs=slabs)
        if slabs:
            items = [item for available in available_stock for item in
                     available.items.all()]
            reserve_items = [item for available in available_stock for item in
                             available.items.filter(is_reserve=True)]
            piece = len(items)
            quantity = sum(item.get_quantity() for item in items)
            reserve_piece = len(reserve_items)
            reserve_quantity = sum(item.get_quantity() for item in reserve_items)
        else:
            piece = sum(available.piece for available in available_stock)
            reserve_piece = sum(available.reserve_piece for available in available_stock)
            quantity = sum(available.quantity for available in available_stock)
            reserve_quantity = sum(available.reserve_quantity for available in available_stock)
        return (piece - reserve_piece), (quantity - reserve_quantity)

    @classmethod
    def update_stock_main_size(cls):
        for stock in cls.objects.all():
            if stock.product.type == 'slab':
                size = []
                for slab in stock.items.all():
                    size.append('%s*%s' % (slab.long, slab.height))
                c = Counter(size)
                max_size, count = c.most_common()[0]
                long, height = max_size.split('*')
                width = 0
            else:
                block = stock.product.block
                long, height, width = sorted([block.long, block.width, block.height], reverse=True)
            stock.main_long = long
            stock.main_height = height
            stock.main_width = width
            stock.save()