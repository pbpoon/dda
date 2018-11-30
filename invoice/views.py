from django import forms
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.contrib import messages
from invoice.form import AssignInvoiceForm
from public.views import GetItemsMixin
from django.views.generic.edit import CreateView, UpdateView, ModelFormMixin
from django.views.generic.base import TemplateResponseMixin, View

from invoice.models import Invoice, Payment, Account, Assign


class InvoiceDetailView(GetItemsMixin, DetailView):
    """
    需要有一个完成收款功能
    """
    model = Invoice
    template_name = 'invoice/detail.html'


class InvoiceListView(ListView):
    model = Invoice
    template_name = 'invoice/list.html'


class AccountDetailView(DetailView):
    model = Account


class AccountListView(ListView):
    model = Account


class AccountCreateView(CreateView):
    model = Account
    fields = ('activate', 'name', 'desc')


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
    template_name = 'invoice/assign_form.html'

    def get(self, *args, **kwargs):
        invoice = get_object_or_404(Invoice, pk=self.kwargs.get('invoice_id'))
        object_list = invoice.items.all()
        payment = get_object_or_404(Payment, pk=self.kwargs.get('payment_id'))
        form = AssignInvoiceForm(initial={'invoice': invoice.id, 'payment': payment.id, 'entry': self.request.user})
        amount = min(invoice.get_due_amount(), payment.get_due_amount())
        form.fields['amount'].widget.attrs['placeholder'] = '最高分配金额：' + str(amount)
        return self.render_to_response({'form': form, 'object_list': object_list, 'object': invoice})

    def post(self, *args, **kwargs):
        form = AssignInvoiceForm(data=self.request.POST)
        invoice = get_object_or_404(Invoice, pk=self.kwargs.get('invoice_id'))
        path = invoice.get_absolute_url()
        if form.is_valid():
            form.save()
            messages.success(self.request, '成功分配款项到该账单')
            return redirect(path)
        else:
            messages.error(self.request, '分配款项错误')
            return self.render_to_response({'form': form})


class PaymentCreateView(CreateView):
    model = Payment
    fields = ('date', 'partner', 'account', 'amount', 'entry')

    def get_invoice(self):
        invoice = get_object_or_404(Invoice, pk=self.kwargs.get('invoice_id'))
        return invoice

    def get_initial(self):
        initial = {
            'entry': self.request.user.id,
            'partner': self.kwargs.get('partner_id')}
        return initial

    def get_context_data(self, **kwargs):
        context = super(PaymentCreateView, self).get_context_data(**kwargs)
        invoice = self.get_invoice()
        context['object'] = invoice
        context['form'].fields['amount'].widget.attrs['placeholder'] = '本单欠：' + str(invoice.get_due_amount())
        context['form'].fields['entry'].widget = forms.HiddenInput()
        context['object_list'] = invoice.items.all() if invoice else None
        return context

    def form_valid(self, form):
        invoice = self.get_invoice()
        form.amount = form.cleaned_data['amount'] * int(invoice.type)
        instance = form.save()
        assign = Assign.objects.create(invoice=invoice, payment=instance, amount=instance.amount,
                                       entry=self.request.user)
        return super(PaymentCreateView, self).form_valid(form)
