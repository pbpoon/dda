from django.apps import AppConfig
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist


class PartnerConfig(AppConfig):
    name = 'partner'

    def ready(self):
        from django.contrib.auth.models import User

        def get_company(self):
            from partner.models import MainInfo
            try:
                return MainInfo.objects.get(pk=1)
            except ObjectDoesNotExist:
                return None

        def _display(self):
            if self.last_name and self.first_name:
                return '%s %s' % (self.last_name, self.first_name)
            return self.get_username()

        UserModel = get_user_model()
        UserModel.add_to_class('get_company', get_company)
        User.add_to_class('__str__', _display)
