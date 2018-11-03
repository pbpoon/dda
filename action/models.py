from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class Action(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, db_index=True, related_name='action',
                             verbose_name='用户')
    verb = models.CharField('动作', max_length=255)
    target_ct = models.ForeignKey(ContentType, blank=True, null=True, related_name='target_obj',
                                  on_delete=models.CASCADE)
    target_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    target = GenericForeignKey('target_ct', 'target_id')
    created = models.DateTimeField('发生时间', auto_now_add=True, db_index=True)

    class Meta:
        ordering = ('created',)