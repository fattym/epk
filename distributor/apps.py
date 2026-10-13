from django.apps import AppConfig


class DistributorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'distributor'

    def ready(self):
        from django.db.models.signals import post_save
        from .models import DistributorProfile, DistributorWallet
        from . import signals as distributor_signals

        def ensure_wallet(sender, instance, created, **kwargs):
            if created:
                DistributorWallet.objects.get_or_create(distributor=instance)

        post_save.connect(ensure_wallet, sender=DistributorProfile,
                          dispatch_uid='distributor.ensure_wallet')
