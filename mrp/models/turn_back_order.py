from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation, ContentType
from django.db import models
from django.urls import reverse
from datetime import datetime

from mrp.models import MrpOrderAbstract, OrderItemBase
from public.fields import OrderField

UOM_CHOICES = (('t', '吨'), ('m3', '立方'), ('m2', '平方'))
OPERATION_TYPE = (('in', '入库'), ('out', '出库'))
STATE_CHOICES = (
    ('draft', '草稿'),
    ('confirm', '确认'),
    ('done', '完成'),
    ('cancel', '取消'),
)


class TurnBackOrder(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    from_order = GenericForeignKey()  # 对应的order

    state = models.CharField('状态', choices=STATE_CHOICES, max_length=20, default='draft')

    reason = models.CharField('原因', max_length=80)
    order = OrderField(order_str='TB', blank=True, verbose_name='单号', default='New', max_length=20)
    warehouse = models.ForeignKey('stock.Warehouse', on_delete=models.CASCADE, verbose_name='接收仓库', blank=True,
                                  null=True, help_text='如果没有指定，将会按原单出库仓库接受')
    handler = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name='经办人',
                                related_name='%(class)s_handler')
    entry = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name='登记人',
                              related_name='%(class)s_entry')
    date = models.DateField('日期', default=datetime.now)
    created = models.DateField('创建日期', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)
    stock_trace = GenericRelation('stock.StockTrace')

    class Meta:
        verbose_name = '回退操作'

    def get_obj(self):
        return self.content_type.model_class().objects.get(pk=self.object_id)

    def get_absolute_url(self):
        return reverse('turn_back_order_detail', args=[self.id])

    def get_delete_url(self):
        return reverse('turn_back_order_delete', args=[self.id])


class TurnBackOrderItem(OrderItemBase):
    order = models.ForeignKey('TurnBackOrder', on_delete=models.CASCADE, related_name='items', verbose_name='对应订单')
    package_list = models.ForeignKey('product.PackageList', on_delete=models.SET_NULL, blank=True, null=True,
                                     verbose_name='码单')

    class Meta:
        verbose_name = '出入库操作明细行'

    def save(self, *args, **kwargs):
        if self.package_list:
            self.piece = self.package_list.get_piece()
            self.quantity = self.package_list.get_quantity()
        super().save(*args, **kwargs)

    def get_location(self):
        return self.location

    def get_location_dest(self):
        return self.location_dest
