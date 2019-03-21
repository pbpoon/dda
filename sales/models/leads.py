from _decimal import Decimal
import collections

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.db.models import Q
from django.urls import reverse

from public.fields import OrderField, LineField
from public.models import HasChangedMixin
from sales.models import Customer

TYPE_CHOICES = (('block', '荒料'), ('slab', '板材'))

SALES_LEADS_STATE_CHOICES = (
    ('0%', '错失'),
    ('10%', '新线索'),
    ('30%', '取得确认'),
    ('70%', '报价阶段'),
    ('90%', '成功在望'),
    ('100%', '赢得'),
)
MISS_REASON_CHOICES = [(i, i) for i in ('价钱差距', '质量不符合', '工程流产', '工程暂停', '换板')]


class SalesLeads(HasChangedMixin, models.Model):
    is_vital = models.BooleanField('置顶', default=False)
    desc = models.CharField('摘要', max_length=200, blank=True, null=True)
    partner = models.ForeignKey(Customer, on_delete=models.SET_NULL, verbose_name='客户', blank=True, null=True)
    state = models.CharField('状态', choices=SALES_LEADS_STATE_CHOICES, max_length=20, default='10%')
    handlers = models.ManyToManyField('auth.User', verbose_name='跟进人',
                                      related_name='%(class)s_handler')
    entry = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name='登记人',
                              related_name='%(class)s_entry')

    miss_reason = models.CharField('错失原因', choices=MISS_REASON_CHOICES, max_length=60,
                                   blank=True, null=True)

    created = models.DateField('创建日期', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)
    comments = GenericRelation('comment.Comment')
    files = GenericRelation('files.Files')
    tasks = GenericRelation('tasks.Tasks')

    start_time = models.DateTimeField('开始时间', blank=True, null=True)
    due_time = models.DateTimeField('截至时间', blank=True, null=True)
    category = models.ForeignKey('product.Category', verbose_name='品种名称', on_delete=models.CASCADE)
    type = ArrayField(base_field=models.CharField(max_length=10, choices=TYPE_CHOICES, default='slab'), blank=True,
                      null=True,
                      verbose_name='类型')
    thickness = ArrayField(base_field=models.DecimalField(max_digits=4, decimal_places=2), blank=True, null=True,
                           verbose_name='厚度规格')
    quantity = models.IntegerField(verbose_name='数量', blank=True, null=True)
    pirce_lt = models.IntegerField('价格(起)', blank=True, null=True)
    pirce_gt = models.IntegerField('价格(止)', blank=True, null=True)
    long_lt = models.IntegerField('长(最低)', blank=True, null=True)
    long_gt = models.IntegerField('长(最高)', blank=True, null=True)
    height_lt = models.IntegerField('高(最低)', blank=True, null=True)
    height_gt = models.IntegerField('高(最高)', blank=True, null=True)

    # 质量要求 用tag来输入，日后可以根据要求配比库存现货
    # 长 高 宽（荒料）
    @property
    def name(self):
        def get_type_display(ts):
            string = ""
            for t in ts:
                if t == 'slab':
                    string += '板材'
                else:
                    string += '荒料'
            return string

        thickness = ",".join(map(lambda x: "%s" % x, self.thickness)) if self.thickness else ""
        _type = get_type_display(self.type) if self.type else ""
        quantity = "=%s" % self.quantity if self.quantity else ""
        return f"{self.category} {_type} {thickness} {quantity}"

    class Meta:
        verbose_name = '销售线索'
        ordering = ('-state', '-created')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('sales_leads_detail', args=[self.id])

    # def get_create_item_url(self):
    #     return reverse('sales_order_item_create', args=[self.id])

    def get_update_url(self):
        return reverse('sales_leads_update', args=[self.id])

    def get_delete_url(self):
        return reverse('sales_order_delete', args=[self.id])

    def get_list_url(self):
        return reverse('sales_leads_list', args=[self.id])

    def filter_stocks(self):
        kw = {}
        if self.category:
            kw.update({'product__block__category': self.category})
        if self.type:
            kw.update({'product__type__in': self.type})
        if self.thickness:
            kw.update({'product__thickness__in': self.thickness})
        if self.long_lt or self.long_gt:
            if self.long_lt and self.long_gt:
                kw.update({'main_long__range': [self.long_lt, self.long_gt]})
            elif self.long_lt and self.long_gt is None:
                kw.update({'main_long__lt': self.long_lt})
            elif self.long_lt is None and self.long_gt:
                kw.update({'main_long__gt': self.long_gt})
        if self.height_lt or self.height_gt:
            if self.height_lt and self.height_gt:
                kw.update({'main_height__range': [self.height_lt, self.height_gt]})
            elif self.height_lt and self.height_gt is None:
                kw.update({'main_height__lt': self.height_lt})
            elif self.height_lt is None and self.height_gt:
                kw.update({'main_height__gt': self.height_gt})

        # if 'block' in self.type and (self.height_lt or self.height_gt):
        #     if self.height_lt and self.height_gt:
        #         kw.update({'main_height__range': [self.height_lt, self.height_gt]})
        #     elif self.height_lt and self.height_gt is None:
        #         kw.update({'main_height_lte': self.height_lt})
        #     elif self.height_lt is None and self.height_gt:
        #         kw.update({'main_height_gte': self.height_gt})
        if kw:
            from stock.models import Stock
            stocks = Stock.objects.filter(**kw)[:20]
            return stocks

        # lst = []
        # for key in ['name__contains', 'phone__contains', 'company__name__contains', 'company__phone__contains', ]:
        #     q_obj = Q(**{key:})
        #     lst.append(q_obj)
        # qs = Partner.objects.filter(reduce(operator.or_, lst))

    def save(self, *args, **kwargs):
        if not self.pk:
            comment = '创建'
        else:
            comment = '修改'
        super().save(*args, **kwargs)
        if comment:
            comment += '线索'
            self.create_comment(**{'comment': comment})
