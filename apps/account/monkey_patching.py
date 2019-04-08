from django.db.models import Q
from django.utils import timezone

@property
def tasks(self):
    from datetime import timedelta
    from tasks.models import Tasks
    now = timezone.now()
    future_start = now + timedelta(days=1)
    future_end = now + timedelta(days=365)

    user_tasks = Tasks.objects.filter(Q(entry=self.id) | Q(handler__in=[self.id]))
    today_tasks_ids = user_tasks.filter(time__year=now.year, time__month=now.month, time__day=now.day).values_list('id',
                                                                                                                   flat=True)
    future_tasks_ids = user_tasks.filter(time__range=(future_start, future_end), is_complete=False).values_list('id', flat=True).order_by(
        'time')[:3]
    delay_tasks_ids = user_tasks.filter(time__lte=now, is_complete=False).values_list('id', flat=True).order_by('-time')[:3]

    lst = list(today_tasks_ids)
    lst.extend(list(future_tasks_ids))
    lst.extend(list(delay_tasks_ids))
    all = Tasks.objects.filter(id__in=lst)
    return all
