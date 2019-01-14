from django.db import models
from django.urls import reverse

from invoice.models import Invoice
from stock.models import Location

PARTNER_TYPE_CHOICES = (
    ('customer', '客户'),
    ('supplier', '供应商'),
    ('production', '生产商'),
    ('service', '运输/服务商'),
    ('invoice', '账单费用'),
)


class Province(models.Model):
    name = models.CharField('名称', max_length=20)
    code = models.IntegerField(primary_key=True, verbose_name='省份id', help_text='用于与市级联动')

    class Meta:
        verbose_name = '省份列表'
        verbose_name_plural = verbose_name
        ordering = ('code',)

    def __str__(self):
        return self.name

    def get_city(self):
        return City.objects.filter(code=self.code)


class City(models.Model):
    id = models.IntegerField('id', primary_key=True)
    name = models.CharField('名称', max_length=20)
    code = models.IntegerField('对应省份id')

    class Meta:
        verbose_name = '城市列表'
        verbose_name_plural = verbose_name
        ordering = ('code', 'id')

    def __str__(self):
        return self.name
    #
    # def get_area(self):
    #     return Area.objects.filter(city=self.id)


class Area(models.Model):
    id = models.IntegerField('id', primary_key=True)
    name = models.CharField('名称', max_length=20)
    city = models.IntegerField('对应市id')

    class Meta:
        verbose_name = '地区'
        verbose_name_plural = verbose_name
        ordering = ('city', 'id')

    def __str__(self):
        return self.name


class InvoicePartnerManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(type='invoice')


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
    entry = models.ForeignKey('auth.User', related_name='%(class)s_entry',
                              verbose_name='登记人', on_delete=models.SET_NULL, null=True, blank=True)
    is_activate = models.BooleanField('启用', default=True)
    company = models.ForeignKey('self', related_name='members', limit_choices_to={'is_company': True},
                                on_delete=models.SET_NULL,
                                null=True, blank=True, verbose_name='所属公司')
    objects = models.Manager()
    invoices = InvoicePartnerManager()

    class Meta:
        verbose_name = '伙伴资料'
        # unique_together = ['phone', 'name']

    def get_address(self):
        if self.province:
            address = self.province.name
            address += '/{}'.format(self.city if self.city else self.province.get_city()[0].name)
            return address
        return None

    def get_title(self):
        return self.get_sex_display() or ""

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        if self.is_company:
            return '{}'.format(self.name)
        else:
            company = ''
            if self.company:
                company = '({}) '.format(self.company.name)
            return '{}{} {}'.format(company, self.name, self.get_title())

    def get_absolute_url(self):
        if self.type == 'customer':
            return reverse('customer_detail', args=[self.id])
        elif self.type == 'supplier':
            reverse('supplier_detail', args=[self.id])
        elif self.type in ('production', 'service'):
            return reverse('pro_ser_supplier_detail', args=[self.id])
        return reverse('partner_detail', args=[self.id])

    def get_location(self):
        """
        这个是用来做mrp等order中，取得partner的类型虚拟库位
        """
        loc, _ = Location.objects.get_or_create(is_virtual=True, name=self.type, usage=self.type,
                                                is_activate=True)
        return loc

    @classmethod
    def get_expenses_partner(cls):
        partner, _ = cls.objects.get_or_create(name='杂费支出', is_company=True, type='invoice', phone='88888888888')
        return partner

    @classmethod
    def get_undercharge_partner(cls):
        partner, _ = cls.objects.get_or_create(name='货款少收/坏账', is_company=True, type='invoice', phone='88888888881')
        return partner

    def get_invoices(self):
        return Invoice.objects.filter(partner=self)[:10]

    def get_can_assign_payments(self):
        return [pay for pay in self.payments.all() if pay.get_balance() > 0]

    def get_balance(self):
        return sum(pay.get_balance() for pay in self.payments.all() if pay.get_balance() > 0)


class InvoicePartner(Partner):
    class Meta:
        verbose_name = '账单账号'
        proxy = True


class MainInfo(models.Model):
    company = models.OneToOneField('partner.Partner', on_delete=models.CASCADE, verbose_name='公司资料', blank=True,
                                   null=True)
    logo = models.ImageField('logo', upload_to='logo', blank=True, null=True)
    address_detail = models.TextField('详细地址')

    class Meta:
        verbose_name = '公司资料'

    def __str__(self):
        return self.company.name

    @property
    def account_detail(self):
        from invoice.models import Account
        accounts = Account.objects.filter(activate=True, account_number__isnull=False)
        html = ""
        for account in accounts:
            if html:
                html += '<br>'
            html += '<span>%s</span>' % (account.display())
        return html

    def get_update_url(self):
        return reverse('company_update', args=[self.id])

    def get_absolute_url(self):
        return reverse('company_detail', args=[self.id])
