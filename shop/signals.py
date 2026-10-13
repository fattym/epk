import logging

logger = logging.getLogger(__name__)


def record_commission_for_release(order):
    """Compute and store the distributor commission owed for an order.

    Escrow flow: the wallet is NOT credited when a payment is confirmed. The
    commission is calculated here and released later by an admin via
    ``credit_distributor_wallet``. Idempotent.
    """
    if not order:
        return 0
    if order.commission_earned and order.commission_earned > 0:
        return order.commission_earned
    total = order.total_commission()
    if total > 0:
        order.commission_earned = total
        order.save(update_fields=['commission_earned'])
    return total


def credit_for_payment(payment, raw=False, **kwargs):
    """Post-save hook for shop.Payment (kept for backward-compatible imports).

    Escrow behaviour: when a payment is confirmed the order funds are marked
    HELD (``fund_status='HELD'``) and the distributor commission is calculated
    but NOT yet paid out. Payout happens on admin release (see
    ``credit_distributor_wallet``), closing the customer -> platform ->
    distributor escrow loop. Idempotent.
    """
    if not payment or payment.status != 'confirmed' or raw:
        return
    order = payment.order
    if order is None:
        return
    record_commission_for_release(order)
    if not order.fund_status or order.fund_status != 'HELD':
        order.fund_status = 'HELD'
        order.save(update_fields=['fund_status'])


def credit_distributor_wallet(order):
    """Release escrowed commission for an order to the linked distributor wallet(s).

    Idempotent: orders that already have a CREDIT transaction are skipped.
    Returns the total commission released.
    """
    from .models import OrderItem
    from distributor.models import DistributorWallet, WalletTransaction

    if WalletTransaction.objects.filter(order=order, transaction_type='CREDIT').exists():
        return 0

    total = 0
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
        total += commission
        credited.append(dist_product.distributor.company_name)

    if credited:
        logger.info(
            'Released KSh %s commission for order #%s to: %s',
            total, order.id, ', '.join(credited),
        )
    return total


def credit_distributor_commission(sender, instance, created, raw=False, **kwargs):
    """post_save handler for shop.Payment -> hold funds / compute commission."""
    credit_for_payment(instance, raw=raw)
