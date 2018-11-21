from decimal import Decimal
from django.db import models
from django.urls import reverse

from purchase.fields import LineField

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
    name = models.CharField('编号', max_length=20, unique=True, db_index=True)
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

    class Meta:
        verbose_name = '荒料编号'
        verbose_name_plural = verbose_name
        unique_together = ('name', 'type', 'thickness')

    def __str__(self):
        thickness = '({})'.format(self.thickness) if self.thickness else ''
        return '{}{}{}'.format(self.name, self.type, thickness)

    def save(self, *args, **kwargs):
        if self.type != 'block' and not self.thickness:
            raise ValueError('产品类型不为荒料时，必须录入厚度规格')
        return super(Product, self).save(*args, **kwargs)

    def get_m3(self):
        if not self.m3:
            return self.long * self.width * self.height * 0.000001
        return self.m3

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.id])

    def get_uom(self):
        return self.uom if self.type == 'block' else 'm2'


class Slab(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, limit_choices_to={'type': 'slab'},
                                verbose_name='板材')
    stock = models.ForeignKey('stock.Stock', on_delete=models.SET_NULL, blank=True, null=True,
                              limit_choices_to={'location__is_virtual': False}, related_name='slabs')
    reserve_stock = models.ForeignKey('stock.Stock', on_delete=models.SET_NULL, blank=True, null=True,
                                      limit_choices_to={'location__is_virtual': False}, related_name='reserve_slabs')
    long = models.SmallIntegerField(verbose_name=u'长', help_text='单位cm')
    height = models.SmallIntegerField(verbose_name=u'高', help_text='单位cm')
    kl1 = models.SmallIntegerField(null=True, blank=True,
                                   verbose_name=u'长1')
    kl2 = models.SmallIntegerField(null=True, blank=True,
                                   verbose_name=u'长2')
    kh1 = models.SmallIntegerField(null=True, blank=True,
                                   verbose_name=u'高1')
    kh2 = models.SmallIntegerField(null=True, blank=True,
                                   verbose_name=u'高2')
    quantity = models.DecimalField('面积(m2)', decimal_places=2, max_digits=4)
    part_number = models.SmallIntegerField('夹号')
    line = LineField(verbose_name='序号', for_fields=['product', 'part_number'], blank=True)

    class Meta:
        verbose_name = '板材'
        verbose_name_plural = verbose_name

    # def __str__(self):
    #     return '{}/板材({})'.format(self.sn, self.thickness)

    def save(self, *args, **kwargs):
        k1 = None
        k2 = None
        if self.kl1 and self.kh1:
            k1 = (self.kl1 * self.kh1) / 10000
        if self.kl2 and self.kh2:
            k2 = (self.kl2 * self.kh2) / 10000
        m2 = (self.long * self.height) / 10000 - k1 - k2
        self.quantity = Decimal('{0:.2f}'.format(m2))
        super(Slab, self).save(*args, **kwargs)


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
    item = models.ForeignKey('PackageList', on_delete=models.CASCADE, related_name='items', verbose_name='码单')
    slab = models.ForeignKey('Slab', on_delete=models.CASCADE, related_name='package_list', verbose_name='板材')
    part_number = models.SmallIntegerField('夹号')
    line = LineField(verbose_name='序号', for_fields=['product', 'part_number'], blank=True)

    class Meta:
        verbose_name = '码单项'
