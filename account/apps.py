from django.apps import AppConfig
from django.contrib.auth import get_user_model


class AccountConfig(AppConfig):
    name = 'account'
    verbose_name = '用户资料'

    def ready(self):
        from .monkey_patching import tasks

        UserModel = get_user_model()
        UserModel.add_to_class('tasks', tasks)
