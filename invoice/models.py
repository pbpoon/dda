from datetime import datetime
from decimal import Decimal
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from purchase.fields import OrderField
from django.contrib.contenttypes.views import shortcut

TYPE_CHOICES = (
    ('-1', '支付'),
    ('1', '收款')
)
USAGE_CHOICES = (
    ('货款', '货款'),
    ('加工费', '加工费'),
    ('运费', '运费'),
    ('装车费', '装车费'),
    ('佣金', '佣金'),
)

STATE_CHOICES = (
    ('draft', '草稿'),
    ('confirm', '确认'),
    ('cancel', '取消'),
)


class CreateInvoice:
    # 创建发票的api
    def __init__(self, order, partner, entry, items_dict_lst, state=None, usage=None, type=None, date=None,
                 due_date=None):
        self.model = OrderInvoiceThrough
        self.invoice_model = Invoice
        self.item_model = InvoiceItem
        self.state = state
        self.order = order
        self.partner = partner
        self.entry = entry
        self.usage = usage if usage else '货款'
        self.type = type if type else '-1'
        self.date = timezone.now() if date is None else date
        self.due_date = due_date
        self.items_dict_lst = items_dict_lst
        self.invoice = self.make_invoice()

    def check_invoice(self):
        order_model = ContentType.objects.get_for_model(self.order)
        # order_invoice_lst = self.model.objects.filter(content_type_id=order_model.id,
        #                                               object_id=self.order.id).values_list('id', flat=True)
        invoice = self.invoice_model.objects.filter(partner=self.partner, usage=self.usage, type=self.type,
                                                    entry=self.entry, to_order__content_type_id=order_model.id,
                                                    to_order__object_id=self.order.id)
        if invoice:
            return invoice[0]
        return None

    def create_invoice(self):
        invoice = self.invoice_model.objects.create(partner=self.partner, usage=self.usage, type=self.type,
                                                    entry=self.entry, due_date=self.due_date, date=self.date)
        for item in self.items_dict_lst:
            item['order'] = invoice
            self.item_model.objects.create(**item)
        self.order.invoices.create(invoice=invoice)
        return invoice

    def make_invoice(self):
        # 先查出有没相同的invoice ##check_invoice()
        # 如果有就直接return
        # 没有就create一条 ##create_invoice()
        comment_detail = {}
        comment_detail['order'] = self.order.order
        if self.check_invoice():
            invoice = self.check_invoice()
            if self.state:
                invoice.state = self.state
                invoice.save()
            comment_detail['method'] = '创建'
        else:
            invoice = self.create_invoice()
            comment_detail['method'] = '更改'

        # 日后可以再添加comment的记录
        comment_detail['state'] = invoice.state
        invoice.comments.create(user=self.entry, comment='由{order}{method}'.format(**comment_detail))
        return invoice


class OrderInvoiceThrough(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    order = GenericForeignKey('content_type', 'object_id')
    invoice = models.ForeignKey('Invoice', on_delete=models.CASCADE, verbose_name='账单', related_name='to_order')

    class Meta:
        verbose_name = '订单与账单关系'

    def get_absolute_url(self):
        return shortcut(self.content_type, self.object_id)


class Invoice(models.Model):
    state = models.CharField('状态', max_length=10, choices=STATE_CHOICES, default='draft')
    order = OrderField(order_str='IV', max_length=26, default='New', db_index=True, verbose_name='订单号码')
    created = models.DateTimeField('创建时间', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)

    from_order = models.ManyToManyField('OrderInvoiceThrough', verbose_name='对应订单', related_name='to_invoice')
    date = models.DateField('日期')
    due_date = models.DateField('到期日', blank=True, null=True)
    partner = models.ForeignKey('partner.Partner', on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name='对方', related_name='%(class)s_partner')
    # payments = models.ManyToManyField('Payment', through='Assign', related_name='assign_invoices')
    entry = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='%(class)s_entry', verbose_name='登记')
    usage = models.CharField('款项用途', choices=USAGE_CHOICES, null=False, max_length=20, default='货款')
    type = models.CharField('支付/收款', choices=TYPE_CHOICES, null=False, max_length=2, default='-1')
    is_paid = models.BooleanField('付讫', default=False)
    comments = GenericRelation('comment.Comment')

    class Meta:
        verbose_name = '账单'
        ordering = ('-created',)

    def get_amount(self):
        return Decimal('{0:.2f}'.format(sum(item.get_amount() for item in self.items.all())))

    def get_due_amount(self):
        # 未付余额
        return self.get_amount() - sum(assign.amount for assign in self.assign_payments.all())

    def get_absolute_url(self):
        return reverse('invoice_detail', args=[self.id])

    def __str__(self):
        return self.order


class InvoiceItem(models.Model):
    order = models.ForeignKey('Invoice', on_delete=models.CASCADE, related_name='items', verbose_name='账单', null=True,
                              blank=True)
    item = models.CharField('项目', max_length=200)
    quantity = models.DecimalField('数量', max_digits=8, decimal_places=2)
    price = models.DecimalField('单价', max_digits=8, decimal_places=2)

    class Meta:
        verbose_name = '账单项'

    def get_amount(self):
        return Decimal('{0:.2f}'.format(self.quantity * self.price))


class Assign(models.Model):
    invoice = models.ForeignKey('Invoice', on_delete=models.CASCADE, verbose_name='账单', related_name='assign_payments')
    payment = models.ForeignKey('Payment', on_delete=models.CASCADE, verbose_name='款项', related_name='assign_invoice')
    amount = models.DecimalField('金额', decimal_places=2, max_digits=10)
    created = models.DateTimeField('创建时间', auto_now_add=True)
    entry = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name='登记')


class Payment(models.Model):
    date = models.DateField('日期')
    partner = models.ForeignKey('partner.Partner', on_delete=models.CASCADE, verbose_name='对方',
                                related_name='payments')
    created = models.DateTimeField('创建时间', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)
    account = models.ForeignKey('Account', on_delete=models.CASCADE, verbose_name='帐户')
    amount = models.DecimalField('金额', decimal_places=2, max_digits=10)
    entry = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name='登记',
                              related_name='%(class)s_entry')

    class Meta:
        verbose_name = '收付款记录'

    def get_absolute_url(self):
        return reverse('invoice_detail', args=[self.id])

    def get_due_amount(self):
        # 可分配的余额
        return self.amount - sum(assign.amount for assign in self.assign_invoice.all())


class Account(models.Model):
    activate = models.BooleanField('启用', default=True)
    name = models.CharField('帐户名称', max_length=20)
    desc = models.CharField('描述', max_length=200)
    created = models.DateTimeField('创建时间', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)

    def get_absolute_url(self):
        return reverse('account_detail', args=[self.id])

    def __str__(self):
        return '{}({})'.format(self.name, self.activate)
