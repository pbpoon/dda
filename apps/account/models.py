from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField('头像', blank=True, null=True, upload_to='user/avatar/%Y%m/', default='logo/logo.jpg')

    class Meta:
        verbose_name = '用户资料'

    def __str__(self):
        return self.user.name


class UserCollectBlock(models.Model):
    block_list = ArrayField(
        base_field=models.IntegerField(blank=True, null=True), null=True, blank=True, verbose_name='编号')
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='collect_block')

    class Meta:
        verbose_name = '用户收集荒料编号'

    def __str__(self):
        return f'{self.user}:{len(self.block_list)}'
