import collections

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation, ContentType
from django.db import models
from django.urls import reverse
from datetime import datetime

from mrp.models import MrpOrderAbstract, OrderItemBase
from public.fields import OrderField
from public.models import HasChangedMixin
from public.stock_operate import StockOperate

UOM_CHOICES = (('t', '吨'), ('m3', '立方'), ('m2', '平方'))
OPERATION_TYPE = (('in', '入库'), ('out', '出库'))
STATE_CHOICES = (
    ('draft', '草稿'),
    ('confirm', '确认'),
    ('done', '完成'),
    ('cancel', '取消'),
)


class TurnBackOrder(HasChangedMixin, models.Model):
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
    comments = GenericRelation('comment.Comment')
    invoices = GenericRelation('invoice.Invoice')
    files = GenericRelation('files.Files')

    class Meta:
        verbose_name = '库存回退'
        ordering = ('-date', '-created')

    def get_obj(self):
        return self.content_type.model_class().objects.get(pk=self.object_id)

    def get_absolute_url(self):
        return reverse('turn_back_order_detail', args=[self.id])

    def get_delete_url(self):
        return reverse('turn_back_order_delete', args=[self.id])

    def __str__(self):
        return '{}/库存回退({})'.format(self.get_obj(), self.order[-8:])

    def get_stock(self):
        return StockOperate(order=self, items=self.items.all())

    def done(self):
        is_done, msg = self.get_stock().handle_stock()
        if is_done:
            form_order = self.get_obj()
            is_cancel, cancel_msg = form_order.cancel()
            self.state = 'done'
            self.save()
            self.create_comment()
            comment = '通过 %s <a herf="%s">%s</a>状态:%s, 取消本订单,原因是：%s,库存已逆向操作成功' % (
                self._meta.verbose_name, self.get_absolute_url(), self, self.state, self.reason)
            form_order.create_comment(**{'comment': comment})
            if not is_cancel:
                return is_cancel, cancel_msg
        return is_done, msg

    def get_total(self):
        """
        template使用方式
        {% for key, item in object.get_total.items %}
        {{ key }}:{% if item.part %}{{ item.part }}夹 / {% endif %}{{ item.piece }}件 / {{ item.quantity }}{{ item.uom }}<br>
        {% endfor %}
        """
        d = collections.defaultdict(lambda: 0)
        total = {}
        for item in self.items.all():
            a = total.setdefault(item.product.get_type_display(), d)
            a['piece'] += item.piece
            a['quantity'] += item.quantity
            a['part'] += item.package_list.get_part() if item.package_list else 0
            a['uom'] = item.uom
        return total

    def get_files(self):
        files = self.files.all()
        if files.count() > 10:
            files = files[:10]
        return files


class TurnBackOrderItem(OrderItemBase):
    order = models.ForeignKey('TurnBackOrder', on_delete=models.CASCADE, related_name='items', verbose_name='对应订单')
    package_list = models.ForeignKey('product.PackageList', on_delete=models.SET_NULL, blank=True, null=True,
                                     verbose_name='码单')

    class Meta:
        verbose_name = '库存回退明细行'

    def save(self, *args, **kwargs):
        if self.package_list:
            self.piece = self.package_list.get_piece()
            self.quantity = self.package_list.get_quantity()
        super().save(*args, **kwargs)

    def get_location(self):
        return self.location

    def get_location_dest(self):
        return self.location_dest
