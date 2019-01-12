from django.apps import AppConfig
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist


#


class PartnerConfig(AppConfig):
    name = 'partner'

    def ready(self):
        def get_company(self):
            from partner.models import MainInfo
            try:
                return MainInfo.objects.get(pk=1)
            except ObjectDoesNotExist:
                return None

        UserModel = get_user_model()
        UserModel.add_to_class('get_company', get_company)
