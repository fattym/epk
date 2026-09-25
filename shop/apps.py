from django.apps import AppConfig


class ShopConfig(AppConfig):
    name = 'shop'

    def ready(self):
        from . import signals
        from django.db.models.signals import post_save
        from .models import Payment
        post_save.connect(signals.credit_distributor_commission, sender=Payment,
                          dispatch_uid='shop.credit_distributor_commission')
