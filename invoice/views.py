from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.contrib import messages
from invoice.form import AssignInvoiceForm
from public.views import GetItemsMixin, OrderItemEditMixin, StateChangeMixin, OrderItemDeleteMixin
from django.views.generic.edit import CreateView, UpdateView, ModelFormMixin
from django.views.generic.base import TemplateResponseMixin, View

from invoice.models import Invoice, Payment, Account, Assign, InvoiceItem
from public.widgets import CheckBoxWidget


class InvoiceDetailView(StateChangeMixin, DetailView):
    """
    需要有一个完成收款功能
    """
    model = Invoice
    template_name = 'invoice/detail.html'

    def get_btn_visible(self, state):
        btn_visible = {}
        if state == 'draft':
            btn_visible.update({'confirm': True, 'cancel': True})
        elif state == 'confirm':
            btn_visible.update({'done': True, 'draft': True})
        elif state == 'done':
            btn_visible.update({'turn_back': True})
        return btn_visible

    def confirm(self):
        return self.object.confirm()

    def done(self):
        return self.object.done()

    def draft(self):
        return self.object.draft()

    def cancel(self):
        return self.object.cancel()


class InvoiceListView(ListView):
    model = Invoice
    template_name = 'invoice/list.html'


class InvoiceItemEditView(OrderItemEditMixin):
    model = InvoiceItem
    fields = '__all__'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['order'].widget = forms.HiddenInput()
        form.fields['order'].initial = self.order
        form.fields['line'].widget = forms.HiddenInput()
        return form


class InvoiceItemDeleteView(OrderItemDeleteMixin):
    model = InvoiceItem


class AccountDetailView(DetailView):
    model = Account


class AccountListView(ListView):
    model = Account


class AccountCreateView(CreateView):
    model = Account
    fields = ('activate', 'name', 'desc')
    template_name = 'form.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['activate'].widget = CheckBoxWidget()
        return form


class PaymentDetailView(DetailView):
    model = Payment


class PaymentListView(ListView):
    model = Payment


class AssignDeleteView(View):
    def post(self, *args, **kwargs):
        assign = get_object_or_404(Assign, pk=self.kwargs.get('assign_id'))
        path = assign.invoice.get_absolute_url()
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


class PaymentEditView(ModelFormMixin, View):
    model = Payment
    fields = ('date', 'partner', 'account', 'type', 'amount', 'entry')
    template_name = 'item_form.html'

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
        context['form'].fields['amount'].widget.attrs['max'] = str(invoice.due_amount)
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
        if form.is_valid():
            if invoice:
                form.type = invoice.type
            instance = form.save()
            if invoice:
                assign = Assign.objects.create(invoice=invoice, payment=instance, amount=instance.amount,
                                               entry=self.request.user)
            form.save()
            msg += '成功'
            messages.success(self.request, msg)
            # return redirect(path)
            return JsonResponse({'state': 'ok', 'url': path})
        msg += '失败'
        return HttpResponse(render_to_string(self.template_name, {'form': form, 'error': msg}))
