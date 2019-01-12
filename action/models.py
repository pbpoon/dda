from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ObjectDoesNotExist


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


class WxConfig(models.Model):
    name = models.CharField('应用名称', max_length=20)
    corp_id = models.CharField(max_length=80)
    agent_id = models.CharField(max_length=80)
    values = JSONField()

    class Meta:
        verbose_name = '微信企业设置'

    def __str__(self):
        return self.name


class WxConf:
    def __init__(self, corp_id=None, agent_id=None):
        self._corp_id = corp_id
        self._agent_id = agent_id
        self.value = self.get_value()

    def get_value(self):
        try:
            return WxConfig.objects.get(agent_id=self._agent_id).values
        except ObjectDoesNotExist:
            return {}

    def __getattr__(self, item):
        return self.value.get(item, None)

