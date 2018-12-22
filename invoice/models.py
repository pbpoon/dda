import datetime
from decimal import Decimal
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.urls import reverse
from django.utils import timezone

from public.fields import OrderField, LineField
from django.contrib.contenttypes.views import shortcut

from public.models import HasChangedMixin

TYPE_CHOICES = (
    ('-1', '付款'),
    ('1', '收款')
)
USAGE_CHOICES = (
    ('货款', '货款'),
    ('加工费', '加工费'),
    ('杂费', '杂费'),
    ('装车费', '装车费'),
    ('佣金', '佣金'),
)

STATE_CHOICES = (
    ('draft', '草稿'),
    ('confirm', '确认'),
    ('cancel', '取消'),
)
UOM_CHOICES = (
    ('t', '吨'),
    ('m3', '立方'),
    ('m2', '平方'),
    ('cart', '车'),
    ('part', '夹'),
    ('piece', '件'),
)


class CreateInvoice:
    # 创建发票的api
    def __init__(self, order, partner, items_dict_lst, state=None, usage=None, type=None, date=None,
                 due_date=None, due_day=None):
        self.invoice_model = Invoice
        self.item_model = InvoiceItem
        self.state = state
        self.order = order
        self.partner = partner
        self.entry = self.order.entry
        self.usage = usage if usage else '货款'
        self.type = type if type else '-1'
        self.date = timezone.now() if date is None else date
        if due_day and date:
            due_date = date + datetime.timedelta(due_day)
        self.due_date = due_date
        self.items_dict_lst = items_dict_lst
        self.invoice = self.make()

    def get_invoice(self):
        order_model = ContentType.objects.get_for_model(self.order)
        # order_invoice_lst = self.model.objects.filter(content_type_id=order_model.id,
        #                                               object_id=self.order.id).values_list('id', flat=True)
        invoice = self.invoice_model.objects.filter(partner=self.partner, usage=self.usage, type=self.type,
                                                    content_type=order_model, object_id=self.order.id)
        if invoice:
            return invoice[0], False
        return self.order.invoices.create(partner=self.partner, usage=self.usage, type=self.type,
                                          entry=self.entry, due_date=self.due_date, date=self.date), True

    def get_or_create_invoice(self):
        invoice, is_create = self.get_invoice()
        invoice.items.all().delete()
        for item in self.items_dict_lst:
            item['order'] = invoice
            self.item_model.objects.create(**item)
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

    def make(self, payment=None):
        # 先查出有没相同的invoice ##check_invoice()
        # 如果有就直接return
        # 没有就create一条 ##create_invoice()
        comment_content = {}
        comment_content['order'] = str(self.order)
        invoice, is_create = self.get_or_create_invoice()
        if is_create:
            comment_content['method'] = '创建'
        else:
            comment_content['method'] = '更改'
        # 日后可以再添加comment的记录
        invoice.comments.create(user=self.entry, content='由{order}{method}'.format(**comment_content))
        if payment:
            self.create_payment(invoice, payment)
            invoice.state = self.state
            invoice.save()
        return invoice


class Invoice(HasChangedMixin, models.Model):
    state = models.CharField('状态', max_length=10, choices=STATE_CHOICES, default='draft')
    order = OrderField(order_str='IV', max_length=26, default='New', db_index=True, verbose_name='订单号码')
    created = models.DateTimeField('创建时间', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    from_order = GenericForeignKey('content_type', 'object_id')

    date = models.DateField('日期')
    due_date = models.DateField('到期日', blank=True, null=True)
    partner = models.ForeignKey('partner.Partner', on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name='对方', related_name='%(class)s_partner')
    # payments = models.ManyToManyField('Payment', through='Assign', related_name='assign_invoices')
    entry = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='%(class)s_entry', verbose_name='登记')
    usage = models.CharField('款项用途', choices=USAGE_CHOICES, null=False, max_length=20, default='货款')
    type = models.CharField('付款/收款', choices=TYPE_CHOICES, null=False, max_length=2, default='-1')
    is_paid = models.BooleanField('付讫', default=False)
    comments = GenericRelation('comment.Comment')

    class Meta:
        verbose_name = '账单'
        ordering = ('-created',)

    def get_obj(self):
        return self.content_type.model_class().objects.get(pk=self.object_id)

    @property
    def amount(self):
        return Decimal('{0:.2f}'.format(sum(item.amount for item in self.items.all())))

    @property
    def due_amount(self):
        # 未付余额
        return self.amount - self.paid_amount

    @property
    def paid_amount(self):
        return sum(assign.amount for assign in self.assign_payments.all())

    def get_absolute_url(self):
        return reverse('invoice_detail', args=[self.id])

    def get_create_item_url(self):
        return reverse('invoice_item_create', args=[self.id])

    def __str__(self):
        return '[{}]{}/金额:{}'.format(self.get_type_display(), self.order, self.amount)

    def confirm(self):
        self.state = 'confirm'
        self.save()
        print(self.changed_data())
        return True, ''

    def done(self):
        if self.due_amount == 0:
            self.state = 'done'
            self.save()
            print(self.changed_data())
            return True, ''
        return False, '该账单下还有金额 {} 未完成付款。'.format(self.due_amount)

    def cancel(self):
        msg = ''
        if self.assign_payments.all():
            amt = sum(ass.amount for ass in self.assign_payments.all())
            msg = '该账单下被分配的付款金额 {} ，将退回付款方名下'.format(amt)
            self.assign_payments.all().delete()
        self.state = 'cancel'
        self.save()
        return True, msg

    def draft(self):
        is_done, msg = self.cancel()
        self.state = 'draft'
        self.save()
        return is_done, msg

    def quick_assign_due_payment(self, partner, account, entry):
        payment = Payment.objects.create(date=datetime.date.today(),
                                         partner=partner,
                                         account=account,
                                         type=self.type,
                                         amount=self.due_amount,
                                         entry=self.entry)
        Assign.objects.create(invoice=self, payment=payment, amount=payment.amount, entry=entry)


class InvoiceItem(HasChangedMixin, models.Model):
    order = models.ForeignKey('Invoice', on_delete=models.CASCADE, related_name='items', verbose_name='账单', null=True,
                              blank=True)
    line = LineField(for_fields=['order'], blank=True, verbose_name='行')
    item = models.CharField('项目', max_length=200)
    quantity = models.DecimalField('数量', max_digits=8, decimal_places=2)
    uom = models.CharField('计量单位', null=False, choices=UOM_CHOICES, max_length=10, default='m2')
    price = models.DecimalField('单价', max_digits=8, decimal_places=2)
    sales_order_item = models.ForeignKey('sales.SalesOrderItem', on_delete=models.CASCADE,
                                         related_name='invoice_items', blank=True, null=True,
                                         verbose_name='销售订单明细行')
    purchase_order_item = models.ForeignKey('purchase.PurchaseOrderItem', on_delete=models.CASCADE,
                                            related_name='invoice_items', blank=True, null=True,
                                            verbose_name='采购订单明细行')

    class Meta:
        verbose_name = '账单项'

    @property
    def amount(self):
        return Decimal('{0:.2f}'.format(self.quantity * self.price))

    @property
    def state(self):
        return self.order.state


class Assign(models.Model):
    invoice = models.ForeignKey('Invoice', on_delete=models.CASCADE, verbose_name='账单', related_name='assign_payments')
    payment = models.ForeignKey('Payment', on_delete=models.CASCADE, verbose_name='款项', related_name='assign_invoice')
    amount = models.DecimalField('金额', decimal_places=2, max_digits=10)
    created = models.DateTimeField('创建时间', auto_now_add=True)
    entry = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name='登记')

    class Meta:
        verbose_name = '收款分配'


class Payment(models.Model):
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

    class Meta:
        verbose_name = '收付款记录'
        ordering = ('-created', 'confirm')

    def __str__(self):
        return '{}/金额 {} @{}'.format(self.get_type_display(), self.amount, self.date)

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

    def done(self):
        self.confirm = True
        self.save()
        for assign in self.assign_invoice.all():
            assign.invoice.done()
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
