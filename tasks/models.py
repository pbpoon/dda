from datetime import datetime, timedelta

import pytz
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils.html import mark_safe
from public.models import HasChangedMixin


class Tasks(HasChangedMixin, models.Model):
    name = models.CharField('提醒标题', max_length=100)
    time = models.DateTimeField('提醒时间')

    is_complete = models.BooleanField('完成', default=False)
    complete_time = models.DateTimeField('完成时间', blank=True, null=True)
    complete_entry = models.ForeignKey('auth.User', on_delete=models.SET_NULL, verbose_name='完成人',
                                       related_name='%(class)s_complete_entry', blank=True, null=True)

    handler = models.ManyToManyField('auth.User', verbose_name='指派经办人',
                                     related_name='%(class)s_handler', blank=True, null=True)

    entry = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name='登记人',
                              related_name='%(class)s_entry')

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    object = GenericForeignKey('content_type', 'object_id')

    created = models.DateField('创建日期', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)

    comments = GenericRelation('comment.Comment')
    files = GenericRelation('files.Files')
    push = GenericRelation('action.SchemeWxPush')

    class Meta:
        verbose_name = '提醒事项'
        ordering = ['-time', '-updated', '-created']

    def __str__(self):
        return self.name

    def get_obj(self):
        return self.content_type.model_class().objects.get(pk=self.object_id)

    def create_comment(self, **kwargs):
        obj = self.get_obj()
        if hasattr(obj, 'create_comment'):
            return self.get_obj().create_comment(**kwargs)

    def set_scheme_push(self):
        self.push.all().delete()
        if not self.is_complete:
            self.push.create(title=self.name, time=self.time, app_name='scheme_push')

    def save(self, *args, **kwargs):
        comment = ""
        new = False
        if not self.pk:
            new = True
            comment = mark_safe('创建 <a href="{url}">%s</a> 提醒事项' % self)
        if kwargs.get('comment'):
            comment += kwargs.pop('comment')
        super().save(*args, **kwargs)
        if new:
            comment = comment.format(url=self.get_absolute_url())
        if comment:
            self.create_comment(**{'comment': comment})
        self.set_scheme_push()

    def get_absolute_url(self):
        return "%s#%s_card" % (self.get_obj().get_absolute_url(), self.id)

    def get_delete_url(self):
        return reverse('tasks_delete', args=[self.id])

    @property
    def id_expired(self):
        now = datetime.utcnow().replace(tzinfo=pytz.timezone('UTC'))
        if now - self.time > timedelta(minutes=1):
            return True
        return False

    def set_complete(self):
        now = datetime.utcnow()# + timedelta(hours=8)
        now = now.replace(tzinfo=pytz.timezone('UTC'))
        state = ''
        if self.is_complete:
            state = '设为：未完成'
            self.is_complete = False
            self.complete_time = None
            self.complete_entry = None
        else:
            state = '完成'
            self.is_complete = True
            self.complete_time = now
            self.complete_entry = self.get_user()
        comment = mark_safe(
            "%s @ %s %s：<a href='%s'>%s</a> 提醒事项" % (self.get_user(), now, state, self.get_absolute_url(), self))
        self.save(**{'comment': comment})
