from datetime import datetime
from django import forms
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.template.loader import render_to_string
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.contrib import messages

from invoice.filters import InvoiceFilter, PaymentFilter
from invoice.form import AssignInvoiceForm, InvoiceForm, PaymentForm
from partner.models import Partner
from public.permissions_mixin_views import DynamicPermissionRequiredMixin
from public.views import GetItemsMixin, OrderItemEditMixin, StateChangeMixin, OrderItemDeleteMixin, ModalOptionsMixin, \
    FilterListView, SentWxMsgMixin
from django.views.generic.edit import CreateView, UpdateView, ModelFormMixin
from django.views.generic.base import TemplateResponseMixin, View

from invoice.models import Invoice, Payment, Account, Assign, InvoiceItem, InvoiceDueDateDefaultSet, PurchaseInvoice, \
    SalesInvoice, ExpensesInvoice
from public.widgets import SwitchesWidget, RadioWidget, DatePickerWidget


class InvoiceDetailView(StateChangeMixin, DetailView):
    model = Invoice
    template_name = 'invoice/detail.html'

    def get_btn_visible(self, state):
        return {'draft': {'confirm': True, 'cancel': True},
                'confirm': {'done': True, 'draft': True},
                'done': {}, 'cancel': {'draft': True}
                }[state]

    def confirm(self):
        return self.object.confirm()

    def done(self):
        return self.object.done()

    def draft(self):
        return self.object.draft()

    def cancel(self):
        return self.object.cancel()


class InvoiceListView(FilterListView):
    model = Invoice
    filter_class = InvoiceFilter
    template_name = 'invoice/list.html'


class ExpensesInvoiceListView(InvoiceListView):
    model = ExpensesInvoice


class ExpensesInvoiceDetailView(InvoiceDetailView):
    model = ExpensesInvoice


class PurchaseInvoiceListView(InvoiceListView):
    model = PurchaseInvoice


class PurchaseInvoiceDetailView(InvoiceDetailView):
    model = PurchaseInvoice


class SalesInvoiceListView(InvoiceListView):
    model = SalesInvoice


class SalesInvoiceDetailView(InvoiceDetailView):
    model = SalesInvoice


class InvoiceEditMixin(DynamicPermissionRequiredMixin):
    model = Invoice
    template_name = 'form.html'
    form_class = InvoiceForm


class InvoiceCreateView(InvoiceEditMixin, CreateView):
    def dispatch(self, request, app_label_lower=None, order_id=None):
        self.object = None
        if app_label_lower:
            app_label, model_name = app_label_lower.split('.')
            self.from_order = apps.get_model(app_label=app_label, model_name=model_name).objects.get(pk=order_id)
        return super().dispatch(request)

    def get_initial(self):
        initial = super().get_initial()
        initial['content_type'] = ContentType.objects.get_for_model(self.from_order)
        initial['object_id'] = self.from_order.id
        initial['entry'] = self.request.user.id
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['partner'] = self.from_order.partner
        return kwargs
    #
    # def get_form(self, form_class=None):
    #     form = super().get_form(form_class)
    #     p = Partner.objects.filter(pk=self.from_order.partner.id)
    #     qs = p.union(Partner.invoices.all())
    #     form.fields['partner'].queryset = qs
    #     return form


class SalesInvoiceCreateView(InvoiceCreateView):
    model = SalesInvoice


class InvoiceUpdateView(InvoiceEditMixin, UpdateView):
    pass


class SalesInvoiceUpdateView(InvoiceUpdateView):
    model = SalesInvoice


class InvoiceItemEditView(OrderItemEditMixin):
    model = InvoiceItem
    fields = '__all__'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['order'].initial = self.order
        form.fields['order'].widget = forms.HiddenInput()
        form.fields['content_type'].widget = forms.HiddenInput()
        form.fields['object_id'].widget = forms.HiddenInput()
        form.fields['line'].widget = forms.HiddenInput()
        return form


class InvoiceItemDeleteView(OrderItemDeleteMixin):
    model = InvoiceItem


class AccountDetailView(DynamicPermissionRequiredMixin, DetailView):
    model = Account


class AccountListView(DynamicPermissionRequiredMixin, ListView):
    model = Account


class AccountCreateView(DynamicPermissionRequiredMixin, CreateView):
    model = Account
    fields = '__all__'
    template_name = 'form.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['activate'].widget = SwitchesWidget()
        form.fields['is_visible'].widget = SwitchesWidget()
        return form


class AccountUpdateView(DynamicPermissionRequiredMixin, UpdateView):
    model = Account
    fields = '__all__'
    template_name = 'form.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['activate'].widget = SwitchesWidget()
        form.fields['is_visible'].widget = SwitchesWidget()
        return form


class PaymentSentWxMixin(SentWxMsgMixin):
    app_name = 'payment'  # 发微信

    def get_url(self):
        return "%s" % (self.request.build_absolute_uri(self.object.get_absolute_url()))

    def get_title(self):
        return '[%s %s] ¥ %.2f [%s %s]' % (
            self.object.account, self.object.get_type_display(), self.object.amount, self.request.user,
            '确认收款' if self.object.confirm else '设成草稿')

    def get_description(self):
        html = '\n[%s]金额:¥%.2f\n' % (self.object.get_type_display(), self.object.amount)
        html += '\n账户:%s' % self.object.account
        html += '\n对方:%s' % self.object.partner
        html += '\n日期:%s' % self.object.date
        now = datetime.now()
        html += '\n登记人:%s @%s' % (self.object.entry, datetime.strftime(now, '%Y/%m/%d %H:%M'))
        return html


class PaymentDetailView(StateChangeMixin, PaymentSentWxMixin, DetailView):
    model = Payment

    def get_btn_visible(self, state):
        return {'draft': {'confirm': True, 'delete': True},
                'confirm': {'draft': True},
                }[state]

    def confirm(self):
        self.object.done()
        self.sent_msg()
        return True, ''

    def draft(self):
        self.sent_msg()
        return self.object.draft()


class PaymentListView(FilterListView):
    model = Payment
    ordering = ('type', 'confirm', '-date')
    filter_class = PaymentFilter
    # def get_queryset(self):
    #     qs = super().get_queryset()
    #     qs = qs.annotate('type')


class PaymentEditView(PaymentSentWxMixin, DynamicPermissionRequiredMixin, ModelFormMixin, View):
    model_permission = ('add',)

    model = Payment
    # fields = ('date', 'partner', 'account', 'type', 'amount', 'entry')
    form_class = PaymentForm
    template_name = 'item_form.html'

    def get_title(self):
        return '[%s %s] ¥ %.2f' % (self.object.account, self.object.get_type_display(), self.object.amount)

    def get_invoice(self):
        if self.kwargs.get('invoice_id'):
            return get_object_or_404(Invoice, pk=self.kwargs.get('invoice_id'))
        return None

    def get_initial(self):
        initial = {
            'entry': self.request.user.id,
            'partner': self.kwargs.get('partner_id')}
        return initial

    def get_context_data(self, **kwargs):
        if kwargs.get('pk'):
            self.object = self.get_object()
        else:
            self.object = None
        context = super().get_context_data(**kwargs)
        invoice = self.get_invoice()
        context['form'].fields['date'].widget.attrs['class'] = 'datepicker'
        context['form'].fields['amount'].widget.attrs['placeholder'] = '本单欠：' + str(invoice.due_amount)
        # context['form'].fields['amount'].widget.attrs['max'] = str(invoice.due_amount)
        context['form'].fields['entry'].widget = forms.HiddenInput()
        context['form'].fields['partner'].widget = forms.HiddenInput()
        if invoice:
            context['form'].fields['type'].widget = forms.HiddenInput()
        return context

    def get(self, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return HttpResponse(render_to_string(self.template_name, context))

    @transaction.atomic()
    def post(self, *args, **kwargs):
        path = self.request.META.get('HTTP_REFERER')
        context = self.get_context_data(**kwargs)
        form = context['form']
        msg = '修改' if self.object else '添加'
        invoice = self.get_invoice()
        files = self.request.FILES.getlist('files')
        if form.is_valid():
            instance = form.save(commit=False)
            if invoice:
                instance.type = invoice.type
            instance.save()
            print(instance)
            self.object = instance
            print('obj', self.object)
            if files:
                desc = form.cleaned_data.get('desc', None)
                from files.models import Files
                for file in files:
                    f = Files(object=instance, content=file, entry=self.request.user, desc=desc)
                    f.save()
            if invoice:
                due_amount = min(invoice.due_amount, instance.amount)
                assign = Assign.objects.create(invoice=invoice, payment=instance, amount=due_amount,
                                               entry=self.request.user)
            instance.create_comment()
            msg += '成功'
            messages.success(self.request, msg)
            print('ready_sent_msg')
            self.sent_msg()
            print('out_sent_msg')
            # return redirect(path)
            return JsonResponse({'state': 'ok', 'url': path})
        msg += '失败'
        return HttpResponse(render_to_string(self.template_name, {'form': form, 'error': msg}))


class PaymentDeleteView(OrderItemDeleteMixin, PaymentSentWxMixin):
    model = Payment

    def get_title(self):
        return '[%s %s] ¥ %.2f [%s 删除]' % (
            self.object.account, self.object.get_type_display(), self.object.amount, self.request.user)

    def get_success_url(self):
        invoice = None
        for assign in self.object.assign_invoice.all():
            invoice = assign.invoice
            break
        if invoice:
            return invoice.get_absolute_url()
        return self.object.partner.get_absolute_url()
        # return self.request.META.get('HTTP_REFERER')

    def delete_after(self):
        return self.sent_msg()


class AssignDeleteView(View):
    def post(self, *args, **kwargs):
        assign = get_object_or_404(Assign, pk=self.kwargs.get('assign_id'))
        # path = assign.invoice.get_absolute_url()
        path = self.request.META.get('HTTP_REFERER')
        assign.delete()
        return redirect(path)


class AssignPaymentFormView(TemplateResponseMixin, View):
    template_name = 'item_form.html'

    def get(self, *args, **kwargs):
        invoice = get_object_or_404(Invoice, pk=self.kwargs.get('invoice_id'))
        payment = get_object_or_404(Payment, pk=self.kwargs.get('payment_id'))
        form = AssignInvoiceForm(initial={'invoice': invoice.id, 'payment': payment.id, 'entry': self.request.user})
        amount = min(invoice.due_amount, payment.get_balance())
        form.fields['amount'].widget.attrs = {'placeholder': '最高分配金额：' + str(amount), 'max': amount, 'min': 0,
                                              'step': 0.01}
        form.fields['amount'].initial = amount
        return HttpResponse(render_to_string(self.template_name, {'form': form}))

    def post(self, *args, **kwargs):
        form = AssignInvoiceForm(data=self.request.POST)
        invoice = get_object_or_404(Invoice, pk=self.kwargs.get('invoice_id'))
        path = invoice.get_absolute_url()
        if form.is_valid():
            obj = form.save(commit=False)
            try:
                assign = Assign.objects.get(invoice=obj.invoice, payment=obj.payment)
                assign.amount += obj.amount
                assign.save()
            except ObjectDoesNotExist:
                obj.save()
            messages.success(self.request, '成功分配款项到该账单')
            return JsonResponse({'state': 'ok', 'url': path})

        else:
            messages.error(self.request, '分配款项错误')
            return HttpResponse(render_to_string(self.template_name, {'form': form}))


# 账单快速少收货款操作
class QuickInvoiceAssignUnderchargePayment(DynamicPermissionRequiredMixin, ModalOptionsMixin):
    model = Invoice

    def do_yes(self, *args):
        account = Account.get_undercharge_account()
        partner = self.object.partner.get_undercharge_partner()
        self.object.quick_assign_due_payment(partner=partner, account=account, entry=self.request.user)
        return True, '已成功登记款项'

    def do_no(self, *args):
        return False, ''

    def get_options(self):
        return [('do_yes', '是'), ('do_no', '否')]

    def get_content(self):
        return '是否登记少收货款,金额:{}'.format(self.object.due_amount)


class InvoiceDueDateDefaultSetListView(FilterListView):
    model = InvoiceDueDateDefaultSet


class InvoiceDueDateDefaultSetDetailView(DynamicPermissionRequiredMixin, DetailView):
    model = InvoiceDueDateDefaultSet


class InvoiceDueDateDefaultSetEditMixin(DynamicPermissionRequiredMixin):
    model = InvoiceDueDateDefaultSet
    fields = '__all__'
    template_name = 'item_form.html'

    def get_success_url(self):
        return reverse('invoice_due_date_default_list')

    def form_valid(self, form):
        self.object = form.save()
        return JsonResponse({'state': 'ok'})


class InvoiceDueDateDefaultSetCreateView(InvoiceDueDateDefaultSetEditMixin, CreateView):
    pass


class InvoiceDueDateDefaultSetUpdateView(InvoiceDueDateDefaultSetEditMixin, UpdateView):
    pass
