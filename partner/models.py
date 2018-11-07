from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

from stock.models import Location

PARTNER_TYPE_CHOICES = (
    ('customer', '客户'),
    ('supplier', '供应商'),
    ('employee', '员工'),
)


class Province(models.Model):
    id = models.SmallIntegerField('id', primary_key=True)
    name = models.CharField('名称', max_length=20)
    province_id = models.SmallIntegerField('省份id', help_text='用于与市级联动')

    class Meta:
        verbose_name = '省份列表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class City(models.Model):
    id = models.SmallIntegerField('id', primary_key=True)
    name = models.CharField('名称', max_length=20)
    father_id = models.SmallIntegerField('对应省份id')

    class Meta:
        verbose_name = '城市列表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Partner(models.Model):
    name = models.CharField('名称', max_length=30, null=False, blank=False)
    is_company = models.BooleanField('公司', default=False)
    type = models.CharField('伙伴类型', choices=PARTNER_TYPE_CHOICES, max_length=20,
                            default='customer')
    phone = models.CharField('联系电话', max_length=20)
    sex = models.CharField('性别', choices=(('male', '先生'), ('female', '女士')), null=True, blank=True, max_length=10)
    province = models.ForeignKey('Province', verbose_name='省份', null=True, blank=True, on_delete=models.SET_NULL)
    city = models.ForeignKey('City', verbose_name='城市', null=True, blank=True, on_delete=models.SET_NULL)
    created = models.DateField('创建日期', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)
    entry = models.ForeignKey(User, related_name='%(class)s_entry',
                              verbose_name='登记人', on_delete=models.SET_NULL, null=True, blank=True)
    is_activate = models.BooleanField('启用', default=True)

    class Meta:
        verbose_name = '伙伴资料'
        unique_together = ['phone', 'name']

    def get_title(self):
        return '先生' if self.sex == 'male' else '女士'

    def __str__(self):
        if self.is_company:
            return '{}'.format(self.name)
        else:
            return '{} {}'.format(self.name, self.get_title())

    def get_absolute_url(self):
        return reverse('partner_detail', args=[self.id])

    def get_location(self):
        """
        is_virtual=True
            先warehouse找，如果有就找该partner下的仓库的is_main的,没有就创建一个
        取得虚拟的供应商或者
        Returns:

        """
        if self.type != 'employee':
            loc, _ = Location.objects.get_or_create(is_virtual=True, name=self.type, usage=self.type,
                                                    is_activate=True)
            return loc
        return None
