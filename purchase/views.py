from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.generic.base import View
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormView, CreateView
from .forms import PurchaseOrderItemForm, PurchaseOrderForm, StateForm
from django.contrib.auth.mixins import LoginRequiredMixin
from product.models import Product
from .models import PurchaseOrder, PurchaseOrderItem
from invoice.models import CreateInvoice

from django.contrib import messages
from braces.views import JsonRequestResponseMixin, CsrfExemptMixin


class PurchaseOrderItemEditView(View):
    def post(self, *args, **kwargs):
        form = PurchaseOrderItemForm(self.request.POST)
        if form.is_valid():
            form.save(commit=False)
            form.entry = self.request.user
            instance = form.save()
            data = {'name': instance.name}
            data['state'] = 'success'
            return JsonResponse(data)
        else:
            return JsonResponse({'state': form.errors})


class StateChangeMixin:
    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_btn_visible(self, state):
        return {s: s != state for s in ('draft', 'confirm', 'cancel')}

    def get_context_data(self, **kwargs):
        state_form = StateForm()
        state = self.object.state
        kwargs.update({'state_form': state_form,
                       'btn_visible': self.get_btn_visible(state)})
        return super(StateChangeMixin, self).get_context_data(**kwargs)

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        post = self.request.POST
        if 'draft' in post:
            return self.draft()
        elif 'confirm' in post:
            return self.confirm()
        elif 'cancel' in post:
            return self.cancel()
        return redirect(self.get_success_url())

    def confirm(self):
        pass
        return redirect(self.get_success_url())

    def cancel(self):
        pass
        return redirect(self.get_success_url())

    def draft(self):
        pass
        return redirect(self.get_success_url())


class GetItemsMixin:
    def get_context_data(self, **kwargs):
        if self.object:
            items = self.object.items.all()
            kwargs.update({'object_list': items})
        return super(GetItemsMixin, self).get_context_data(**kwargs)


class PurchaseOrderListView(ListView):
    model = PurchaseOrder
    template_name = 'purchase/order/list.html'
    paginate_by = 10


class PurchaseOrderDetailView(StateChangeMixin, DetailView):
    model = PurchaseOrder
    template_name = 'purchase/order/detail.html'

    def get_context_data(self, **kwargs):
        items = self.object.items.all()
        comments = self.object.comments.all()
        # kwargs.update({'object_list': items, 'comments': comments})
        return super(PurchaseOrderDetailView, self).get_context_data(**kwargs)

    def confirm(self):
        comment = ''
        products = (item.product for item in self.object.items.all())
        for p in products:
            p.activate = True
            p.save()
        obj = self.get_object()
        comment = '{}状态 =>'.format(obj.state)
        obj.state = 'confirm'
        obj.save()
        # 日后生产invoice
        comment += obj.state
        obj.comments.create(user=self.request.user, comment=comment)

        items_dict_lst = [{'item': str(item.product), 'price': item.price, 'quantity': item.get_quantity()} for item in
                          obj.items.all()]
        CreateInvoice(order=obj, partner=obj.partner, entry=obj.entry, items_dict_lst=items_dict_lst)
        messages.info(self.request, '设置订单{}设置成 确认 状态'.format(obj.order))
        return super(PurchaseOrderDetailView, self).confirm()

    def draft(self):
        obj = self.get_object()
        obj.state = 'draft'
        obj.save()
        messages.info(self.request, '设置订单{}设置成 草稿 状态'.format(obj.order))
        return super(PurchaseOrderDetailView, self).draft()


class PurchaseOrderCreateView(CreateView):
    model = PurchaseOrder
    fields = ('date', 'partner', 'handler', 'currency', 'uom')
    template_name = 'purchase/order/form.html'

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.entry = self.request.user
        instance.save()
        return super(PurchaseOrderCreateView, self).form_valid(form)


class PurchaseOrderCreateViewSetpOne(LoginRequiredMixin, ListView, FormView):
    model = PurchaseOrderItem
    form_class = PurchaseOrderItemForm
    template_name = 'purchase/order/form.html'
    success_url = reverse_lazy('purchase_order_create_one')

    def get_queryset(self):
        qs = super(PurchaseOrderCreateViewSetpOne, self).get_queryset()
        qs.filter(entry=self.request.user)
        go_next = True if qs else False
        return qs

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.entry = self.request.user
        instance.save()
        return super(PurchaseOrderCreateViewSetpOne, self).form_valid(form)


class PurchaseOrderCreateViewSetpTwo(LoginRequiredMixin, CreateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'purchase/order/form2.html'
    success_url = reverse_lazy('purchase_order_detail')

    def get_context_data(self, **kwargs):
        items = PurchaseOrderItem.objects.filter(entry=self.request.user, order__isnull=True)
        kwargs.update({'object_list': items})
        return super(PurchaseOrderCreateViewSetpTwo, self).get_context_data(**kwargs)

    def form_valid(self, form):
        # 先检查该名称的product是否已经存在，如果已经存在就raise，sent一个message
        # 如果没有就用该资料创建一个产品（activate是false），并绑定到item
        instance = form.save(commit=False)
        instance.entry = self.request.user
        items = PurchaseOrderItem.objects.filter(entry=self.request.user, order__isnull=True)
        errors = []
        for item in items:
            fields_name = ('uom', 'weight', 'long', 'height', 'm3')
            default = {i.name: getattr(item, i.name) for i in item._meta.fields if i.name in fields_name}
            product, is_create = Product.objects.get_or_create(name=item.name, type=item.type, defaults=default)
            if not is_create:
                errors.append('编号：{}#,的荒料已经存在，请确保荒料的编号不重复！'.format(product.name))
            item.product = product
        if errors:
            # 日后更改
            instance.save()
            for item in items:
                item.order = instance
                item.save()
            comment = "订单{}创建!".format(instance.order)
            instance.comments.create(user=self.request.user, comment=comment)
            messages.success(self.request, '订单{}已创建！'.format(instance.order))
        else:
            for error in errors:
                messages.add_message(self.request, messages.ERROR, error)
                redirect(self.request.path)
        return redirect('purchase_order_detail', instance.id)
