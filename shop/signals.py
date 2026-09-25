import logging

logger = logging.getLogger(__name__)


def credit_for_payment(payment, raw=False, **kwargs):
    """Credit the linked distributor wallet(s) when a Payment is confirmed.

    The cash collected from the parent flows to the global "Coding Clubs Kenya"
    account (via M-Pesa). This only *reflects* the balance: for every order
    item whose product is a resold distributor product, the per-unit
    commission stored on the Product is credited to that distributor's wallet.
    Idempotent: already-credited payments are skipped.
    """
    if not payment:
        return
    if payment.status != 'confirmed':
        return

    order = payment.order
    if order is None:
        return

    from .models import OrderItem
    from distributor.models import DistributorWallet, WalletTransaction

    if order.commission_earned and order.commission_earned > 0:
        # Already credited.
        return

    if WalletTransaction.objects.filter(order=order, transaction_type='CREDIT').exists():
        return

    total_commission = 0
    credited = []
    for item in OrderItem.objects.select_related(
        'variant__product__linked_distributor_product__distributor'
    ).filter(order=order):
        product = item.variant.product
        dist_product = product.linked_distributor_product
        if not dist_product or product.commission_amount is None:
            continue
        commission = product.commission_amount * item.quantity
        if commission <= 0:
            continue
        wallet, _ = DistributorWallet.objects.get_or_create(distributor=dist_product.distributor)
        wallet.credit(
            commission,
            order=order,
            reference=f'Order #{order.id} item {item.id}',
        )
        total_commission += commission
        credited.append(dist_product.distributor.company_name)

    if total_commission > 0:
        order.commission_earned = total_commission
        order.save(update_fields=['commission_earned'])

    if credited:
        logger.info(
            'Credited KSh %s commission for order #%s to: %s',
            total_commission, order.id, ', '.join(credited),
        )


def credit_distributor_commission(sender, instance, created, raw=False, **kwargs):
    """post_save handler for shop.Payment -> credit distributor wallets."""
    credit_for_payment(instance, raw=raw)
