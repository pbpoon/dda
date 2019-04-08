from datetime import datetime, timedelta

from django.http import JsonResponse
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
    # TODO: 点击完成任务后跳出反馈框，可以写入反馈，或者新建后续提醒


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
            ('1h', '1小时后'),
            ('2h', '2小时后'),
            ('3h', '3小时后'),
            ('--', '------'),
            ('1d', '1天后'),
            ('3d', '3天后'),
            ('7d', '1周后'),
            ('30d', '1个月后'),
        )

    def get_success_url(self):
        return False

    def get_content(self):
        content = "推迟 %s 的提醒时间在：" % self.object
        return content

    def do_option(self, time):
        state = time[-1]
        delay_time = int(time[:-1])
        self.object = self.get_object()
        if state == 'd':
            self.object.time = self.object.time + timedelta(days=delay_time)
        elif state == 'h':
            self.object.time = self.object.time + timedelta(hours=delay_time)
        else:
            return False, ''
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
        lst = ['电话联系', '开单', '发图片', '报价', '寄样板', '选荒料', '到访本地', '接送', '查账']
        task_id = self.forwarded.get('id')
        if task_id:
            from tasks.models import Tasks
            task = Tasks.objects.get(pk=task_id)
            if task.name not in lst:
                lst.append(task.name)
        return lst

    def create(self, text):
        lst = self.get_list()
        lst.append(text)
        return text


class SalesLeadsTaskCreateView(TasksCreateView):
    pass
