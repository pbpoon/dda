import calendar
import datetime
from decimal import Decimal
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from public.fields import OrderField, LineField
from django.contrib.contenttypes.views import shortcut

from public.models import HasChangedMixin, OrderItemSaveCreateCommentMixin

TYPE_CHOICES = (
    ('-1', '付款'),
    ('1', '收款')
)
USAGE_CHOICES = (
    ('货款', '货款'),
    ('加工费', '加工费'),
    ('杂费', '杂费'),
    ('运输费', '运输费'),
    ('装车费', '装车费'),
    ('佣金', '佣金'),
)

STATE_CHOICES = (
    ('draft', '草稿'),
    ('confirm', '确认'),
    ('cancel', '取消'),
    ('done', '完成'),
)
UOM_CHOICES = (
    ('t', '吨'),
    ('m3', '立方'),
    ('m2', '平方'),
    ('cart', '车'),
    ('part', '夹'),
    ('piece', '件'),
)

DUE_DATE_DEFAULT_CHOICES = (('0', '立刻'),
                            ('7', '7天后'),
                            ('15', '15天后'),
                            ('30', '30天后'),
                            ('end_of_month', '月底'),
                            ('end_of_year', '年底'),)


class Invoice(HasChangedMixin, models.Model):
    state = models.CharField('状态', max_length=10, choices=STATE_CHOICES, default='draft')
    order = OrderField(order_str='IV', max_length=26, default='New', db_index=True, verbose_name='订单号码')
    created = models.DateTimeField('创建时间', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    from_order = GenericForeignKey('content_type', 'object_id')

    date = models.DateField('日期')
    due_date = models.DateField('到期日')
    partner = models.ForeignKey('partner.Partner', on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name='对方', related_name='%(class)s_partner')
    # payments = models.ManyToManyField('Payment', through='Assign', related_name='assign_invoices')
    entry = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='%(class)s_entry', verbose_name='登记')
    usage = models.CharField('款项用途',  max_length=50)
    type = models.CharField('付款/收款', choices=TYPE_CHOICES, null=False, max_length=2, default='-1')
    comments = GenericRelation('comment.Comment')

    monitor_fields = ['state', 'partner', 'usage', 'type', 'date', 'due_date']

    class Meta:
        verbose_name = '账单'
        ordering = ('-created',)

    def get_obj(self):
        return self.content_type.model_class().objects.get(pk=self.object_id)

    @property
    def quantity(self):
        return Decimal('{0:.2f}'.format(sum(item.quantity for item in self.items.all())))

    @property
    def amount(self):
        return Decimal('{0:.2f}'.format(sum(item.amount for item in self.items.all())))

    @property
    def due_amount(self):
        # 未付余额
        return self.amount - self.paid_amount

    @property
    def confirm_due_amount(self):
        # 未付余额
        return self.amount - self.confirm_amount

    @property
    def confirm_amount(self):
        return sum(assign.amount for assign in self.assign_payments.filter(payment__confirm=True))

    @property
    def paid_amount(self):
        return sum(assign.amount for assign in self.assign_payments.all())

    def get_absolute_url(self):
        return reverse('invoice_detail', args=[self.id])

    def get_update_url(self):
        return reverse('invoice_update', args=[self.id])

    def get_create_item_url(self):
        return reverse('invoice_item_create', args=[self.id])

    @property
    def all_payment_confirm(self):
        for assign in self.assign_payments.all():
            if not assign.payment.confirm:
                return False
        return True

    def __str__(self):
        display = '已' if self.state == 'done' else '应'
        return '{}{}{}/金额:{}'.format(display, self.get_type_display(), self.order, self.amount)

    def confirm(self, **kwargs):
        self.state = 'confirm'
        self.save()
        self.create_comment(**kwargs)
        return True, ''

    def done(self, **kwargs):
        if self.due_amount == 0 and self.all_payment_confirm:
            self.state = 'done'
            self.save()
            self.create_comment(**kwargs)
            if self.content_type.model in ('salesorder', 'purchaseorder'):
                comment = '完成账单:<a href="%s">%s</a>, 金额：%s' % (
                    self.get_absolute_url(), self, self.amount)
                self.from_order.done(**{'comment': comment})
            return True, ''
        return False, '该账单下还有金额 {} 未完成付款。'.format(self.due_amount)

    def cancel(self, **kwargs):
        msg = ''
        if self.assign_payments.all():
            amt = sum(ass.amount for ass in self.assign_payments.all())
            msg = '该账单下被分配的付款金额 {} ，将退回付款方名下,可分配到其他账单'.format(amt)
            self.assign_payments.all().delete()
        self.state = 'cancel'
        self.save()
        self.create_comment(**kwargs)
        return True, msg

    def draft(self, **kwargs):
        is_done, msg = self.cancel()
        self.state = 'draft'
        self.save()
        self.create_comment(**kwargs)
        return is_done, msg

    def quick_assign_due_payment(self, partner, account, entry):
        payment = Payment.objects.create(date=datetime.date.today(),
                                         partner=partner,
                                         account=account,
                                         type=self.type,
                                         amount=self.due_amount,
                                         entry=self.entry)
        Assign.objects.create(invoice=self, payment=payment, amount=payment.amount, entry=entry)


class InvoiceItem(OrderItemSaveCreateCommentMixin, models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    from_order_item = GenericForeignKey('content_type', 'object_id')

    order = models.ForeignKey('Invoice', on_delete=models.CASCADE, related_name='items', verbose_name='账单', null=True,
                              blank=True)
    line = LineField(for_fields=['order'], blank=True, verbose_name='行')
    item = models.CharField('项目', max_length=200)
    quantity = models.DecimalField('数量', max_digits=8, decimal_places=2)
    uom = models.CharField('计量单位', null=False, choices=UOM_CHOICES, max_length=10, default='m2')
    price = models.DecimalField('单价', max_digits=8, decimal_places=2)
    # sales_order_item = models.ForeignKey('sales.SalesOrderItem', on_delete=models.CASCADE,
    #                                      related_name='invoice_items', blank=True, null=True,
    #                                      verbose_name='销售订单明细行')
    # purchase_order_item = models.ForeignKey('purchase.PurchaseOrderItem', on_delete=models.CASCADE,
    #                                         related_name='invoice_items', blank=True, null=True,
    #                                         verbose_name='采购订单明细行')
    monitor_fields = ['item', 'quantity', 'uom', 'price']

    class Meta:
        verbose_name = '账单项'
        ordering = ('line',)

    @property
    def amount(self):
        return Decimal('{0:.2f}'.format(self.quantity * self.price))

    @property
    def state(self):
        return self.order.state

    # def save(self, *args, **kwargs):
    #     super().save(*args, **kwargs)
    #     logs = self.get_logs()
    #     self.order.create_comment(**{'comment': logs})

    def make_dict(self):
        return {self.item: {'item': self.item, 'quantity': self.quantity, 'price': self.price}}


class Assign(HasChangedMixin, models.Model):
    invoice = models.ForeignKey('Invoice', on_delete=models.CASCADE, verbose_name='账单', related_name='assign_payments')
    payment = models.ForeignKey('Payment', on_delete=models.CASCADE, verbose_name='款项', related_name='assign_invoice')
    amount = models.DecimalField('金额', decimal_places=2, max_digits=10)
    created = models.DateTimeField('创建时间', auto_now_add=True)
    entry = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name='登记')

    class Meta:
        verbose_name = '收款分配'

    @property
    def real_amount(self):
        return self.amount * int(self.payment.type)

    def save(self, *args, **kwargs):
        if not self.pk:
            comment = '把 <a href="%s">%s</a> 的款项分配到本账单, 金额:%s' % (
                self.payment.get_absolute_url(), self.payment, self.amount)
            self.invoice.create_comment(**{'comment': comment})
            paymen_comment = '分配到账单 <a href="%s">%s</a> , 金额:%s' % (
                self.invoice.get_absolute_url(), self.invoice, self.amount)
            self.payment.create_comment(**{'comment': paymen_comment})
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        comment = '<s>把 <a href="%s">%s</a> 的款项分配到本账单, 金额:%s </s>移除' % (
            self.payment.get_absolute_url(), self.payment, self.amount)
        self.invoice.create_comment(**{'comment': comment})
        comment = '<s>取消分配账单 <a href="%s">%s</a> , 金额:%s </s>' % (
            self.invoice.get_absolute_url(), self.invoice, self.amount)
        self.payment.create_comment(**{'comment': comment})
        super().delete(*args, **kwargs)


class Payment(HasChangedMixin, models.Model):
    date = models.DateField('日期')
    partner = models.ForeignKey('partner.Partner', on_delete=models.CASCADE, verbose_name='对方',
                                related_name='payments')
    created = models.DateTimeField('创建时间', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)
    account = models.ForeignKey('Account', on_delete=models.CASCADE, verbose_name='帐户')
    type = models.CharField('支付/收款', choices=TYPE_CHOICES, null=False, max_length=2, default='-1')
    amount = models.DecimalField('金额', decimal_places=2, max_digits=10)
    entry = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name='登记',
                              related_name='%(class)s_entry')
    confirm = models.BooleanField('确认款项', default=False)
    comments = GenericRelation('comment.Comment')

    class Meta:
        verbose_name = '收付款记录'
        ordering = ('-created', 'confirm')

    @property
    def real_amount(self):
        return self.amount * int(self.type)

    def get_state(self):
        return '确认' if self.confirm else '待确认'

    def __str__(self):
        return '{}[{}]{}/金额 {} @{}'.format(self.get_state(), self.account, self.get_type_display(), self.amount,
                                           self.date)

    @property
    def state(self):
        if self.confirm:
            return 'confirm'
        return 'draft'

    def get_state_display(self):
        if self.confirm:
            return '已{}'.format(self.get_type_display())
        return '待{}'.format(self.get_type_display())

    def get_absolute_url(self):
        return reverse('payment_detail', args=[self.id])

    def get_balance(self):
        # 可分配的余额
        return self.amount - sum(assign.amount for assign in self.assign_invoice.all())

    #
    # def get_undercharge_partner_account(self):
    #     partner = self.partner.get_undercharge_partner()
    #     account = self.account.get_undercharge_account()
    #     return partner, account

    def done(self, **kwargs):
        self.confirm = True
        self.save()
        self.create_comment(**kwargs)
        commnet = '确认款项 <a href="%s">%s</a>,更新本账单' % (self.get_absolute_url(), self)
        for assign in self.assign_invoice.all():
            assign.invoice.done(**{'comment': commnet})
        return True, ''

    def draft(self, **kwargs):
        self.confirm = False
        self.save()
        self.create_comment(**kwargs)
        commnet = '款项 <a href="%s">%s</a> 取消 确认状态,更新本账单' % (self.get_absolute_url(), self)
        for assign in self.assign_invoice.all():
            if assign.invoice.state == 'done':
                assign.invoice.confirm(**{'comment': commnet})
        return True, ''


class Account(models.Model):
    activate = models.BooleanField('启用', default=True)
    name = models.CharField('帐户名称', max_length=20)
    desc = models.CharField('描述', max_length=200)
    created = models.DateTimeField('创建时间', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)
    is_visible = models.BooleanField('显示', default=True)

    def get_absolute_url(self):
        return reverse('account_detail', args=[self.id])

    def __str__(self):
        desc = '(%s)' % (self.desc) if self.desc else ''
        return '{}'.format(self.name, desc)

    @classmethod
    def get_expense_account(cls):
        account, _ = cls.objects.get_or_create(name='杂费支出', desc='杂费支出', is_visible=False)
        return account

    @classmethod
    def get_undercharge_account(cls):
        account, _ = cls.objects.get_or_create(name='货款少收', desc='货款少收', is_visible=False)
        return account


class InvoiceDueDateDefaultSet(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name='对应order', unique=True,
                                     limit_choices_to={'model__in': (
                                         'salesorder', 'purchaseorder', 'movelocationorder', 'productionorder',
                                         'inoutorder', 'inventoryorder')})
    default = models.CharField('默认值选项', choices=DUE_DATE_DEFAULT_CHOICES, max_length=20)
    updated = models.DateField('更新日期', auto_now=True)

    class Meta:
        verbose_name = '订单账单限期默认设置'

    def get_due_date(self, date):
        default = self.default
        try:
            days = int(default)
            return date + datetime.timedelta(days=days)
        except Exception as e:
            year, month = date.year, date.month
            if default == 'end_of_month':
                firstDayWeekDay, monthRange = calendar.monthrange(year, month)
            elif default == 'end_of_year':
                firstDayWeekDay, monthRange = calendar.monthrange(year, 12)
            lastDay = datetime.date(year=year, month=month, day=monthRange)
            return lastDay

    @classmethod
    def get_default_due_date(cls, order_model_name, date):
        try:
            default_set = cls.objects.get(content_type__model=order_model_name)
            return default_set.get_due_date(date)
        except ObjectDoesNotExist:
            return date


class CreateInvoice:
    """
    如果对应的订单创建后，有传state，就设置该state
    创建逻辑：
    如果有相关（同一个对应订单，同用途，同type，并且是state=draft，cancel）就返回，否则创建
    把item更新

    更改state逻辑：
    如果对应的state变为cancel，如果本state不为完成，可把本state设置cancel

    due_date逻辑：
        如果是销售订单：创建invoice后，如果有提货记录，就把due时间设置为提货记录天。
        如果没有提货记录，就不设置。
        如果是由提货记录创建的invoice，就只设置该invoice是due

        采购订单：
            设置为确认后的30天
    """

    # 创建发票的api
    def __init__(self, order, partner, items_dict, state=None, usage=None, type=None,
                 due_date=None, payment=None):
        self.invoice_model = Invoice
        self.item_model = InvoiceItem
        self.state = state
        self.order = order
        self.partner = partner
        self.entry = self.order.entry
        self.usage = usage if usage else self.order.invoice_usage
        self.type = type if type else '-1'
        self.date = getattr(self.order, 'date', datetime.date.today())
        self.due_date = self.get_default_due_date() if due_date is None else due_date
        self.items_dict = items_dict
        self.payment = payment
        self.invoice = self.make()

    def get_default_due_date(self):
        return InvoiceDueDateDefaultSet.get_default_due_date(self.order._meta.model_name, self.date)

    def get_invoice(self):
        order_model = ContentType.objects.get_for_model(self.order)
        # order_invoice_lst = self.model.objects.filter(content_type_id=order_model.id,
        #                                               object_id=self.order.id).values_list('id', flat=True)
        invoice = self.invoice_model.objects.filter(Q(state='cancel') | Q(state='draft'), partner=self.partner,
                                                    usage=self.usage, type=self.type,
                                                    content_type=order_model, object_id=self.order.id, )
        if invoice:
            return invoice[0], False
        return self.order.invoices.create(partner=self.partner, usage=self.usage, type=self.type,
                                          entry=self.entry, due_date=self.due_date, date=self.date), True

    def get_or_create_invoice(self):
        invoice, is_create = self.get_invoice()
        items = invoice.items.all()
        update_list = []
        for item in items:
            if item.item in self.items_dict:
                item.line = self.items_dict[item.item]['line']
                item.quantity = self.items_dict[item.item]['quantity']
                item.price = self.items_dict[item.item]['price']
                item.from_order_item = self.items_dict[item.item]['from_order_item']
                item.save()
                update_list.append(item.item)
            else:
                item.delete()
        for k, v in self.items_dict.items():
            if k not in update_list:
                v['order'] = invoice
                self.item_model.objects.create(**v)
        return invoice, is_create

    def create_payment(self, invoice, payment):
        payment = Payment.objects.create(date=datetime.date.today(),
                                         partner=payment['partner'],
                                         account=payment['account'],
                                         type=invoice.type,
                                         amount=invoice.amount,
                                         entry=self.entry)
        Assign.objects.create(invoice=invoice, payment=payment, amount=payment.amount, entry=self.entry)
        return True

    def make(self):
        # 先查出有没相同的invoice ##check_invoice()
        # 如果有就直接return
        # 没有就create一条 ##create_invoice()
        invoice, is_create = self.get_or_create_invoice()
        if is_create:
            method = '创建'
        else:
            method = '修改'
        if self.state:
            invoice.state = self.state
        if self.payment:
            self.create_payment(invoice, self.payment)
        # 日后可以再添加comment的记录
        # logs = invoice.get_logs()
        comment = '通过 %s <a href="%s">%s</a> 对本账单进行 %s<br>%s' % (self.order._meta.verbose_name,
                                                                 self.order.get_absolute_url(), self.order, method,
                                                                 invoice.format_logs(invoice.all_data()))
        # if logs:
        #     comment += '<br>%s' % logs
        invoice.save()
        invoice.create_comment(**{'comment': comment})
        return invoice
