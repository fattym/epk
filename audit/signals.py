from django.apps import apps
from django.contrib.contenttypes.models import ContentType

from .middleware import get_current_request
from .models import AuditLog

SENSITIVE_MODELS = {
    'accounts': ['User'],
    'fees': ['Invoice', 'Payment'],
    'assessment': ['CompetencyAssessment'],
    'recruitment': ['Offer', 'ScoreCard'],
    'shop': ['Order'],
}

SENSITIVE_SNAPSHOT_FIELDS = {
    'fees.Invoice': ['status', 'amount'],
    'fees.Payment': ['amount', 'method'],
    'assessment.CompetencyAssessment': ['level_achieved', 'teacher_comment'],
    'recruitment.Offer': ['status'],
    'recruitment.ScoreCard': ['rating', 'recommendation'],
    'accounts.User': ['role', 'is_active', 'school', 'email'],
}


def _content_type(model_cls):
    try:
        return ContentType.objects.get_for_model(model_cls, for_concrete_model=False)
    except Exception:
        return None


def _school_for_instance(instance):
    """Best-effort extraction of the tenant (school) for an auditable object."""
    school = getattr(instance, 'school', None)
    if school is not None:
        return school
    try:
        invoice = getattr(instance, 'invoice', None)
        if invoice is not None and getattr(invoice, 'school_id', None):
            return invoice.school
    except Exception:
        pass
    return None


def log_action(action, instance=None, model_cls=None, object_id=None,
               object_repr=None, school=None, field=None, before=None,
               after=None, user=None):
    """Record a single audit-log entry."""
    request = get_current_request()
    if user is None and request is not None:
        user = getattr(request, 'user', None)
        if user and not getattr(user, 'is_authenticated', False):
            user = None
    if school is None and instance is not None:
        school = _school_for_instance(instance)
    if school is None and request is not None:
        school = getattr(getattr(request, 'user', None), 'school', None)

    ip = None
    user_agent = ''
    if request is not None:
        ip = request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR')
        if ip and ',' in ip:
            ip = ip.split(',')[0].strip()
        user_agent = request.META.get('HTTP_USER_AGENT', '')

    if model_cls is not None:
        ct = _content_type(model_cls)
    elif instance is not None:
        ct = _content_type(instance.__class__)
    else:
        ct = None

    if object_id is None:
        object_id = getattr(instance, 'pk', None)
    if object_repr is None:
        object_repr = str(instance)[:255] if instance is not None else ''

    AuditLog.objects.create(
        school=school,
        user=user,
        action=action,
        content_type=ct,
        object_id=object_id or '',
        object_repr=object_repr,
        field=field or '',
        before=before,
        after=after,
        ip_address=ip,
        user_agent=user_agent,
    )


def _snapshot(instance):
    model_cls = instance.__class__
    key = f'{model_cls._meta.app_label}.{model_cls._meta.model_name}'
    fields = SENSITIVE_SNAPSHOT_FIELDS.get(key)
    if not fields:
        return None
    return {f: getattr(instance, f) for f in fields}


def _install_signal_handlers():
    """Wire post_save/post_delete signals onto every sensitive model.

    Called once from AppConfig.ready().  Each model gets its own dispatch_uid
    so re-importing is safe.
    """
    from django.db.models.signals import post_delete, post_save
    from django.dispatch import receiver

    def attach(model_cls):
        uid_base = f'audit_{model_cls._meta.app_label}_{model_cls._meta.model_name}'

        @receiver(post_save, sender=model_cls, dispatch_uid=uid_base + '_save')
        def _post_save(sender, instance, created, **kwargs):
            try:
                log_action(
                    'create' if created else 'update',
                    instance=instance,
                    before=None if created else _snapshot(instance),
                    after=_snapshot(instance),
                )
            except Exception:
                pass

        @receiver(post_delete, sender=model_cls, dispatch_uid=uid_base + '_delete')
        def _post_delete(sender, instance, **kwargs):
            try:
                log_action('delete', instance=instance, after=None)
            except Exception:
                pass

    for app_label, model_names in SENSITIVE_MODELS.items():
        app_config = apps.app_configs.get(app_label)
        if app_config is None:
            continue
        for model_name in model_names:
            model_cls = app_config.get_model(model_name)
            if model_cls is not None:
                attach(model_cls)
