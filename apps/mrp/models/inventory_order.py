import collections

from decimal import Decimal
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models import Q
from django.urls import reverse
from datetime import datetime

from public.fields import OrderField, LineField
from public.models import HasChangedMixin
from public.stock_operate import StockOperate

TYPE_CHOICES = (('block', '荒料'), ('semi_slab', '毛板'), ('slab', '板材'))
UOM_CHOICES = (('t', '吨'), ('m3', '立方'), ('m2', '平方'))
OPERATION_TYPE = (('in', '入库'), ('out', '出库'))
STATE_CHOICES = (
    ('draft', '草稿'),
    ('confirm', '确认'),
    ('done', '完成'),
    ('cancel', '取消'),
)


class InventoryOrder(HasChangedMixin, models.Model):
    name = models.CharField('盘点简述', max_length=100)
    state = models.CharField('状态', choices=STATE_CHOICES, max_length=20, default='draft')

    order = OrderField(order_str='INV', blank=True, verbose_name='单号', default='New', max_length=20)
    warehouse = models.ForeignKey('stock.Warehouse', on_delete=models.CASCADE, verbose_name='仓库', blank=True,
                                  null=True, help_text='盘点的仓库')
    product_type = models.CharField('产品类型', max_length=10, choices=TYPE_CHOICES, blank=True, null=True)
    handler = models.ManyToManyField('auth.User', verbose_name='经办人',
                                     related_name='%(class)s_handler')
    entry = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name='登记人',
                              related_name='%(class)s_entry')
    date = models.DateField('日期', default=datetime.now)
    created = models.DateField('创建日期', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)
    comments = GenericRelation('comment.Comment')
    files = GenericRelation('files.Files')
    tasks = GenericRelation('tasks.Tasks')

    class Meta:
        verbose_name = '盘点库存'
        ordering = ('-created',)

    def get_absolute_url(self):
        return reverse('inventory_order_detail', args=[self.id])

    def get_create_item_url(self):
        return reverse('inventory_order_new_item_create', args=[self.id])

    def get_delete_url(self):
        return reverse('inventory_order_delete', args=[self.id])

    def get_all_items(self):
        items = list(self.items.all())
        items.extend(list(self.new_items.all()))
        return items

    def get_files(self):
        files = self.files.all()
        if files.count() > 10:
            files = files[:10]
        return files

    # def get_total(self):
    #     """
    #     template使用方式
    #     {% for key, item in object.get_total.items %}
    #     {{ key }}:{% if item.part %}{{ item.part }}夹 / {% endif %}{{ item.piece }}件 / {{ item.quantity }}{{ item.uom }}<br>
    #     {% endfor %}
    #     """
    #     total = {}
    #     for item in self.get_all_items():
    #         d = collections.defaultdict(lambda: 0)
    #         d['piece'] += item.piece
    #         d['quantity'] += item.quantity
    #         d['part'] += item.package_list.get_part() if item.package_list else 0
    #         d['uom'] = item.uom
    #         total[item.product.get_type_display()] = d
    #     return total

    def __str__(self):
        return self.name

    def get_stock(self):
        # 把相等或未盘点的剔出
        # items = list(self.items.exclude(Q(report='is_equal') | Q(report=None)))
        items = [item for item in self.items.all() if item.state != 0]
        new_items = self.new_items.all()
        # change_loc_items = self.items.filter(report='is_equal')
        # if change_loc_items:
        #     items.extend(list(change_loc_items))
        if new_items:
            items.extend(list(new_items))
        return StockOperate(self, items)

    def done(self, **kwargs):
        is_done, msg = self.get_stock().handle_stock()
        if is_done:
            self.state = 'done'
            self.save()
            self.create_comment(**kwargs)
        return is_done, msg

    def confirm(self):
        if any((item for item in self.items.all() if not item.is_check)):
            return False, '有明细行没有进行盘点'
        self.state = 'confirm'
        self.save()
        return True, ''

    def draft(self):
        if self.state == 'confirm':
            self.state = 'draft'
            self.save()
            return True, ''
        return False, ''


class InventoryOrderItem(models.Model):
    order = models.ForeignKey('InventoryOrder', on_delete=models.CASCADE, related_name='items', verbose_name='对应订单')
    line = LineField(for_fields=['order'], blank=True, verbose_name='行')
    is_check = models.BooleanField('已盘', default=False)
    # report = models.CharField('情况报告', choices=(('is_equal', '与原数据相符'), ('is_lose', '丢失,已不在库的'),
    #                                            ('not_equal', '数据不符(下方输入数据)'), ('change_loc', '位置有变动')), max_length=10,
    #                           default='is_equal')
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE, verbose_name='产品')
    old_location = models.ForeignKey('stock.Location', related_name='%(class)s_old_location', verbose_name='原库位',
                                     on_delete=models.DO_NOTHING, blank=True, null=True)
    # now_location = models.ForeignKey('stock.Location', related_name='%(class)s_now_location', verbose_name='现库位',
    #                                  on_delete=models.DO_NOTHING, blank=True, null=True)
    location = models.ForeignKey('stock.Location', related_name='%(class)s_location', verbose_name='库位',
                                 on_delete=models.DO_NOTHING, blank=True, null=True)
    location_dest = models.ForeignKey('stock.Location', related_name='%(class)s_dest_location', verbose_name='目标库位',
                                      on_delete=models.DO_NOTHING, blank=True, null=True,
                                      limit_choices_to={'is_virtual': False})
    old_piece = models.IntegerField('原件数', default=1)
    old_quantity = models.DecimalField('原数量', decimal_places=2, max_digits=10)
    now_piece = models.IntegerField('现件数', blank=True, null=True)
    now_quantity = models.DecimalField('现数量', decimal_places=2, max_digits=10, blank=True, null=True)
    piece = models.IntegerField('件数', blank=True, null=True)
    quantity = models.DecimalField('数量', decimal_places=2, max_digits=10, blank=True, null=True)
    uom = models.CharField('计量单位', null=False, choices=UOM_CHOICES, max_length=10, default='t')
    old_package_list = models.ForeignKey('product.PackageList', on_delete=models.SET_NULL, blank=True, null=True,
                                         verbose_name='原库码单', related_name='%(class)s_old_package_list')
    now_package_list = models.ForeignKey('product.PackageList', on_delete=models.SET_NULL, blank=True, null=True,
                                         verbose_name='现码单', related_name='%(class)s_now_package_list')
    package_list = models.ForeignKey('product.PackageList', on_delete=models.SET_NULL, blank=True, null=True,
                                     verbose_name='码单')
    ps = models.CharField('备注', max_length=120, blank=True, null=True)
    entry = models.ForeignKey('auth.User', on_delete=models.SET_NULL, verbose_name='登记人',
                              related_name='%(class)s_entry', blank=True, null=True)

    class Meta:
        verbose_name = '盘点库存明细行'
        ordering = ('line',)

    #
    # @property
    # def report(self):
    #     if self.state == 0:
    #         return 'is_equal'
    #     else:
    #         return 'not_equal'

    @property
    def is_done(self):
        if any(((self.piece and self.quantity), self.report)):
            return True
        return False

    @property
    def state(self):
        # if self.report == 'not_equal':
        n_p = self.now_piece or 0
        n_q = self.now_quantity or 0
        p = (n_p - self.old_piece)
        q = round(n_q, 2) - round(self.old_quantity, 2)
        if p > 0 or q > 0:
            return 1
        elif p < 0 or q < 0:
            return -1
        return 0

    # @property
    # def change_loc(self):
    #     if self.old_location != self.now_location:
    #         return True
    #     return False

    def get_diff_piece(self):
        n_p = self.now_piece or 0
        piece = abs(n_p - self.old_piece)
        return piece

    def get_diff_quantity(self):
        n_q = self.now_quantity or 0
        quantity = abs(n_q - self.old_quantity)
        return quantity

    def get_diff_slab_ids(self):
        if self.product.type == 'slab':
            old_slab_ids = self.old_package_list.items.values_list('slab', flat=True)
            now_slab_ids = self.now_package_list.items.values_list('slab', flat=True)
            diff_slab_ids = set(old_slab_ids) ^ set(now_slab_ids)
            return diff_slab_ids
        return False

    # 如果选择是未盘点
    # def set_None(self):
    #     self.now_piece = None
    #     self.now_quantity = None
    #     self.piece = None
    #     self.quantity = None
    #
    # # 如果盘点为相等，就把现在的数量等于之前的数量
    # # 并且如果盘点的是毛板，有码单的，就把盘点的数量
    # def set_is_equal(self):
    #     self.now_piece = self.old_piece
    #     self.now_quantity = self.old_quantity
    #     self.piece = self.old_piece
    #     self.quantity = self.old_quantity
    #     self.location = self.old_location
    #     self.location_dest = self.now_location
    #     if self.old_package_list:
    #         slab_ids_list = [item.get_slab_id() for item in self.old_package_list.items.all()]
    #         self.package_list.update(self.package_list, slab_ids_list)
    #         self.now_package_list.update(self.now_package_list, slab_ids_list)
    #     self.location, self.location_dest = self.old_location, self.now_location or self.old_location
    #
    #     # 如果盘点选项是 is_lose就把now的数据设置为0，把实际的数据设置为old的数据
    #
    # def set_is_lose(self):
    #     self.now_piece = 0
    #     self.now_quantity = 0
    #     self.piece = self.old_piece
    #     self.quantity = self.old_quantity
    #     self.location = self.old_location
    #     self.location_dest = self.old_location.get_inventory_location()
    #     if self.old_package_list:
    #         slab_ids_list = [item.get_slab_id() for item in self.old_package_list.items.all()]
    #         if slab_ids_list:
    #             self.now_package_list.update(self.now_package_list, slab_ids_list)
    #     self.location, self.location_dest = self.old_location, self.old_location.get_inventory_location()
    #
    # def set_not_equal(self):
    #     if self.now_piece == 0:
    #         self.report = 'is_lose'
    #         return self.set_is_lose()
    #     elif self.now_piece == self.old_piece:
    #         self.report = 'is_equal'
    #         return self.set_is_equal()
    #     if self.now_package_list:
    #         self.now_quantity = self.now_package_list.get_quantity()
    #         self.now_piece = self.now_package_list.get_piece()
    #     self.piece = 0 if self.product.type == 'block' else self.get_diff_piece()
    #     self.quantity = self.get_diff_quantity()
    #     if self.old_package_list:
    #         self.package_list.update(self.package_list, self.get_diff_slab_ids())
    #
    #     n_p = self.now_piece or 0
    #     n_q = self.now_quantity or 0
    #     if (n_p - self.old_piece) > 0 or (n_q - self.old_quantity) > 0:
    #         self.location, self.location_dest = self.old_location.get_inventory_location(), self.now_location
    #     else:
    #         self.location, self.location_dest = self.old_location.get_inventory_location(), self.now_location

    # def update_package_list(self):
    #     if self.now_package_list:
    #         self.now_piece = self.now_package_list.get_piece()
    #         self.now_quantity = self.now_package_list.get_quantity()
    #         self.piece = self.get_diff_piece()
    #         self.quantity = self.get_diff_quantity()
    #         self.package_list.update(self.package_list, self.get_diff_slab_ids())

    def save(self, *args, **kwargs):
        if self.pk:
            if self.product.type == 'semi_slab':
                if self.product.semi_slab_single_qty:
                    single_qty = self.product.semi_slab_single_qty
                else:
                    from stock.models import Stock
                    stock = Stock.objects.get(product=self.product, location=self.old_location)
                    single_qty = stock.quantity / stock.piece
                self.now_quantity = self.now_piece * single_qty
            if self.now_package_list:
                self.now_piece = self.now_package_list.get_piece()
                self.now_quantity = self.now_package_list.get_quantity()
            self.piece = self.get_diff_piece()
            self.quantity = self.get_diff_quantity()
            if self.package_list:
                self.package_list.update(self.package_list, self.get_diff_slab_ids())

        inv = self.old_location.get_inventory_location()

        n_p = self.now_piece or 0
        n_q = self.now_quantity or 0
        p = (n_p - self.old_piece)
        q = round(n_q, 2) - round(self.old_quantity, 2)
        # if p > 0 or q > 0:
        #     return 1
        # elif p < 0 or q < 0:
        #     return -1
        # return 0
        if p < 0 or q < 0:
            self.location, self.location_dest = self.old_location, inv
        elif p > 0 or q > 0:
            self.location, self.location_dest = inv, self.old_location
        else:
            self.location, self.location_dest = self.old_location, self.old_location

        super().save(*args, **kwargs)


class InventoryOrderNewItem(models.Model):
    order = models.ForeignKey('InventoryOrder', on_delete=models.CASCADE, related_name='new_items', verbose_name='对应订单')
    line = LineField(for_fields=['order'], blank=True, verbose_name='行')
    block = models.ForeignKey('product.Block', on_delete=models.CASCADE, verbose_name='荒料编号', null=True, blank=True)
    product_type = models.CharField('产品类型', max_length=10, choices=TYPE_CHOICES)
    thickness = models.DecimalField('厚度规格', max_digits=5, decimal_places=2, null=True, blank=True)
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE, verbose_name='产品', blank=True, null=True)
    piece = models.IntegerField('实际件数', blank=True, null=True)
    quantity = models.DecimalField('实际数量', decimal_places=2, max_digits=10, blank=True, null=True)
    location = models.ForeignKey('stock.Location', related_name='%(class)s_location', verbose_name='库位',
                                 on_delete=models.DO_NOTHING, blank=True, null=True)
    location_dest = models.ForeignKey('stock.Location', related_name='%(class)s_location_dest', verbose_name='实际库位',
                                      on_delete=models.DO_NOTHING, limit_choices_to={'is_virtual': False})
    uom = models.CharField('计量单位', null=False, choices=UOM_CHOICES, max_length=10, default='t')
    package_list = models.ForeignKey('product.PackageList', on_delete=models.SET_NULL, blank=True, null=True,
                                     verbose_name='码单')
    draft_package_list = models.ForeignKey('product.DraftPackageList', on_delete=models.SET_NULL, blank=True, null=True,
                                           verbose_name='草稿码单')
    ps = models.CharField('备注', max_length=120, blank=True, null=True)
    entry = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name='登记人',
                              related_name='%(class)s_entry')

    class Meta:
        verbose_name = '盘点新增产品'
        ordering = ('line',)

    @property
    def is_done(self):
        return True
