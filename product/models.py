from decimal import Decimal

import decimal
from django.db import models
from django.urls import reverse

from public.fields import LineField
from stock.models import Stock
# from stock.stock_operate import StockOperate

TYPE_CHOICES = (('block', '荒料'), ('semi_slab', '毛板'), ('slab', '板材'))
UOM_CHOICES = (('t', '吨'), ('m3', '立方'))


class Category(models.Model):
    name = models.CharField(max_length=20, null=False, unique=True,
                            db_index=True, verbose_name=u'品种名称')
    created = models.DateField(auto_now_add=True, verbose_name=u'添加日期')

    class Meta:
        verbose_name = u'品种信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Quarry(models.Model):
    name = models.CharField(max_length=20, null=False, unique=True,
                            verbose_name=u'矿口名称')
    desc = models.CharField(max_length=200, verbose_name=u'描述信息')
    created = models.DateField(auto_now_add=True, verbose_name=u'添加日期')
    updated = models.DateField(auto_now=True, verbose_name=u'更新日期')

    class Meta:
        verbose_name = u'矿口信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Batch(models.Model):
    name = models.CharField(max_length=20, unique=True, db_index=True,
                            verbose_name=u'批次编号')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    updated = models.DateTimeField('更新日期', auto_now=True)

    class Meta:
        verbose_name = u'批次'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField('编号', max_length=20, db_index=True)
    type = models.CharField('类型', max_length=10, choices=TYPE_CHOICES, default='block')
    thickness = models.DecimalField('厚度规格', max_digits=5, decimal_places=2, null=True, blank=True)
    batch = models.ForeignKey('Batch', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='批次')
    category = models.ForeignKey('Category', null=True, blank=True, verbose_name='品种名称', on_delete=models.SET_NULL)
    quarry = models.ForeignKey('Quarry', null=True, blank=True, verbose_name='矿口', on_delete=models.SET_NULL)
    weight = models.DecimalField('重量', max_digits=5, decimal_places=2, null=True)
    long = models.IntegerField('长', null=True, blank=True)
    width = models.IntegerField('宽', null=True, blank=True)
    height = models.IntegerField('高', null=True, blank=True)
    m3 = models.DecimalField('立方', null=True, max_digits=5, decimal_places=2, blank=True)
    uom = models.CharField('荒料计量单位', null=False, choices=UOM_CHOICES, max_length=10, default='t')
    updated = models.DateTimeField('更新日期', auto_now=True)
    created = models.DateTimeField('创建日期', auto_now_add=True)
    activate = models.BooleanField('启用', default=False)
    semi_slab_single_qty = models.DecimalField('毛板单件平方', null=True, max_digits=5, decimal_places=2, blank=True)

    class Meta:
        verbose_name = '荒料编号'
        verbose_name_plural = verbose_name
        unique_together = ('name', 'type', 'thickness')

    def __str__(self):
        thickness = '({})'.format(self.thickness) if self.thickness else ''
        return '{}{}{}'.format(self.name, self.get_type_display(), thickness)

    def save(self, *args, **kwargs):
        if self.type != 'block' and not self.thickness:
            raise ValueError('产品类型不为荒料时，必须录入厚度规格')
        return super(Product, self).save(*args, **kwargs)

    def get_m3(self):
        if self.type == 'block' and self.uom == 't':
            m3 = self.weight / decimal.Decimal(2.8)
            return Decimal('{0:.2f}'.format(m3))

        elif not self.m3 and self.long and self.width and self.height:
            m3 = self.long * self.width * self.height * 0.000001
            return Decimal('{0:.2f}'.format(m3))
        return Decimal('{0:.2f}'.format(0))

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.id])

    def get_uom(self):
        return self.uom if self.type == 'block' else 'm2'

    def create_product(self, type, thickness):
        if type == self.type:
            raise ValueError('后续产品类型不能相同！')
        default = {f.name: getattr(self, f.name) for f in self._meta.fields if
                   f.name not in ['id', 'name', 'type', 'thickness', 'updated', 'created', 'activate']}
        product, is_create = self.__class__.objects.get_or_create(name=self.name, type=type, thickness=thickness,
                                                                  defaults=default)
        return product

    def get_available(self, location=None):
        return Stock.get_available(product=self, location=location)


class SlabAbstract(models.Model):
    # product = models.ForeignKey('Product', on_delete=models.CASCADE, limit_choices_to={'type': 'slab'},
    #                             verbose_name='板材')

    long = models.SmallIntegerField(verbose_name=u'长', help_text='cm')
    height = models.SmallIntegerField(verbose_name=u'高', help_text='cm')
    kl1 = models.SmallIntegerField(null=True, blank=True, verbose_name=u'长1')
    kl2 = models.SmallIntegerField(null=True, blank=True, verbose_name=u'长2')
    kh1 = models.SmallIntegerField(null=True, blank=True, verbose_name=u'高1')
    kh2 = models.SmallIntegerField(null=True, blank=True, verbose_name=u'高2')
    # quantity = models.DecimalField('面积(m2)', decimal_places=2, max_digits=4)
    part_number = models.SmallIntegerField('夹号')
    line = LineField(verbose_name='序号', for_fields=['part_number'], blank=True)

    class Meta:
        abstract = True
        ordering = ('part_number', 'line')

    def __str__(self):
        k1 = ""
        k2 = ""
        if self.kl1 and self.kh1:
            k1 = '({}*{})'.format(self.kl1, self.kh1)
        if self.kl2 and self.kh2:
            k2 = "({}*{})".format(self.kl2, self.kh2)

        m2 = "{}*{}".format(self.long, self.height)
        if k1:
            m2 += k1
        if k2:
            m2 += k2
        return m2

    def get_quantity(self):
        k1 = 0
        k2 = 0
        if self.kl1 and self.kh1:
            k1 = (self.kl1 * self.kh1) / 10000
        if self.kl2 and self.kh2:
            k2 = (self.kl2 * self.kh2) / 10000
        m2 = (self.long * self.height) / 10000 - k1 - k2
        return Decimal('{0:.2f}'.format(m2))


class Slab(SlabAbstract):
    stock = models.ForeignKey('stock.Stock', on_delete=models.SET_NULL, blank=True, null=True,
                              limit_choices_to={'location__is_virtual': False}, related_name='slabs')
    reserve_stock = models.ForeignKey('stock.Stock', on_delete=models.SET_NULL, blank=True, null=True,
                                      limit_choices_to={'location__is_virtual': False}, related_name='reserve_slabs')

    verbose_name = '板材'
    verbose_name_plural = verbose_name


class PackageList(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='package_listed', verbose_name='产品')

    class Meta:
        verbose_name = '码单'

    def get_quantity(self):
        return sum(item.slab.quantity for item in self.items.all())

    def get_part(self):
        return len({item.part_number for item in self.items.all()})

    def get_piece(self):
        return len(self.items.all())


class PackageListItem(models.Model):
    order = models.ForeignKey('PackageList', on_delete=models.CASCADE, related_name='items', verbose_name='码单')
    slab = models.ForeignKey('Slab', on_delete=models.CASCADE, related_name='package_list', verbose_name='板材')
    part_number = models.SmallIntegerField('夹号')
    line = LineField(verbose_name='序号', for_fields=['order', 'part_number'], blank=True)

    class Meta:
        verbose_name = '码单项'


class DraftPackageList(models.Model):
    name = models.CharField('编号', max_length=20, db_index=True)
    entry = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name='登记人',
                              related_name='%(class)s_entry')
    created = models.DateField('创建日期', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = "草稿码单"

    def get_absolute_url(self):
        return reverse('package_list_draft_detail', args=[self.id])

    def get_item_edit_url(self):
        return reverse('package_list_draft_item_edit')

    def get_total_piece(self, number=None):
        qs = self.items.all()
        if number:
            qs = qs.filter(part_number=number)
        return qs.count()

    def get_total_quantity(self, number=None):
        qs = self.items.all()
        if number:
            qs = qs.filter(part_number=number)
        quantity = sum(item.get_quantity() for item in qs)
        return quantity

    def get_total_part_number(self, number=None):
        qs = self.items.all()
        if number:
            qs = qs.filter(part_number=number)
        part = {item.part_number for item in qs}
        return len(part)


class DraftPackageListItem(SlabAbstract):
    order = models.ForeignKey('DraftPackageList', on_delete=models.CASCADE, related_name='items',
                              verbose_name='码单')
    line = LineField(verbose_name='序号', for_fields=['order', 'part_number'], blank=True)

    class Meta:
        verbose_name = "草稿码单行"
