from datetime import datetime, timedelta

import pytz
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.utils.html import mark_safe
from public.views import ContentTypeEditMixin, OrderFormInitialEntryMixin, OrderItemDeleteMixin, ModalOptionsMixin
from tasks.forms import TasksCreateForm
from tasks.models import Tasks
from dal import autocomplete


class TasksListView(ListView):
    model = Tasks


class TasksDetailView(DetailView):
    model = Tasks


class TasksCreateView(ContentTypeEditMixin, OrderFormInitialEntryMixin, CreateView):
    model = Tasks
    form_class = TasksCreateForm
    fields = None


class TasksUpdateView(ContentTypeEditMixin, OrderFormInitialEntryMixin, UpdateView):
    model = Tasks
    form_class = TasksCreateForm
    fields = None


class TasksDeleteView(OrderItemDeleteMixin):
    model = Tasks

    def delete_after(self):
        time = self.object.time + timedelta(hours=8)
        comment = "删除了 %s@%s 提醒事项" % (self.object, datetime.strftime(time, "%Y-%m-%d %H:%M"))
        self.object.create_comment(**{'comment': comment})


class TasksDelayView(ModalOptionsMixin):
    model = Tasks

    def get_options(self):
        return (
            (1, '1天后'),
            (3, '3天后'),
            (7, '1周后'),
            (30, '1个月后'),
        )

    def get_success_url(self):
        return False

    def get_content(self):
        content = "推迟 %s 的提醒时间在：" % self.object
        return content

    def do_option(self, day):
        day = int(day)
        self.object = self.get_object()
        self.object.time = self.object.time + timedelta(days=day)
        self.object.save()
        comment = mark_safe('推迟 <a href="%s">%s</a> 提醒时间到:%s' % (
            self.object.get_absolute_url(), self.object, self.object.time + timedelta(hours=8)
        ))
        self.object.create_comment(**{'comment': comment})
        return True, comment


class TaskSetCompleteView(View):
    model = Tasks

    def post(self, *args, **kwargs):
        pk = self.request.POST.get('pk')
        if pk:
            item = self.model.objects.get(pk=pk)
            # if item.is_complete:
            #     item.is_complete = False
            # else:
            #     item.is_complete = True
            #     item.complete_time = datetime.utcnow().replace(tzinfo=pytz.timezone('UTC'))
            # item.save()
            item.set_complete()
            html = render_to_string('tasks/task_card_panel.html', {'task': item})
            html = mark_safe(html)
            return JsonResponse({'state': 'ok', 'check': item.is_complete, 'complete_time': item.complete_time,
                                 'html': html})
        return JsonResponse({'state': 'error'})


class TasksAutocompleteListView(autocomplete.Select2ListView):

    def get_list(self):
        return ['电话联系', '开单', '发图片', '报价', '寄样板', '选荒料', '到访本地', '接送', '查账']

    def create(self, text):
        lst = self.get_list()
        lst.append(text)
        return text


class SalesLeadsTaskCreateView(TasksCreateView):
    pass
