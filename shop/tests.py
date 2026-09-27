from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from accounts.models import User, ParentLearner
from tenants.models import School
from academics.models import Term
from distributor.models import DistributorProfile, DistributorProduct, DistributorWallet, WalletTransaction
from shop.models import Product, ProductCategory, Order, OrderItem, Payment


class ParentShopCommissionTest(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name='Test School', code='TS001', address='x', phone='0700', email='s@x.com')
        # Distributor
        self.dist_user = User.objects.create_user(
            email='dist@ccke.com', password='pass1234', role='DISTRIBUTOR', school=self.school)
        self.profile = DistributorProfile.objects.create(
            user=self.dist_user, company_name='Coding Clubs Kenya')
        self.dist_product = DistributorProduct.objects.create(
            distributor=self.profile, name='Geometry Set', unit_price=Decimal('100.00'),
            category='Stationery', is_active=True, available_stock=50)
        # Parent + learner
        self.parent = User.objects.create_user(
            email='parent@ccke.com', password='pass1234', role='PARENT', school=self.school)
        self.learner = User.objects.create_user(
            email='learner@ccke.com', password='pass1234', role='STUDENT', school=self.school)
        ParentLearner.objects.create(parent=self.parent, learner=self.learner, school=self.school)
        # School product with a fixed 50 markup over the distributor unit price
        self.category = ProductCategory.objects.create(school=self.school, name='Stationery')
        # An active term is required for the fee-balance payment method.
        Term.objects.create(school=self.school, name='Term 1', start_date='2026-01-01',
                            end_date='2026-06-01', academic_year='2025/2026', is_current=True)
        self.product = Product.objects.create(
            school=self.school, category=self.category, name='Geometry Set (Resale)',
            description='A geometry set', price=150,
            linked_distributor_product=self.dist_product,
            markup_type='fixed', markup_value=50, is_reseller_listing=True, is_active=True)

    def _api(self, user):
        client = APIClient()
        token = str(AccessToken.for_user(user))
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return client

    def test_checkout_creates_order_and_commission_is_credited(self):
        client = self._api(self.parent)

        # 1. Place the order (checkout). Product has no variants -> backend creates a Default one.
        resp = client.post('/api/shop/orders/', {
            'learner': self.learner.id,
            'items': [{'product': self.product.id, 'quantity': 2}],
        }, format='json')
        self.assertEqual(resp.status_code, 201, resp.json())
        order = Order.objects.get()
        self.assertEqual(order.total_amount, Decimal('300.00'))  # 150 * 2
        self.assertEqual(order.commission_earned, Decimal('0.00'))  # not credited until paid

        # 2. Record an M-Pesa-style payment as initiated, then confirm it.
        Payment.objects.create(order=order, method='mpesa', amount=order.total_amount, status='initiated')
        confirm_url = f'/api/shop/orders/{order.id}/confirm-payment/'
        resp = client.post(confirm_url, {}, format='json')
        self.assertEqual(resp.status_code, 200, resp.json())
        self.assertEqual(resp.json()['order_status'], 'paid')

        # 3. Escrow: funds are HELD, the commission is calculated but NOT yet
        #    paid out to the distributor wallet.
        order.refresh_from_db()
        self.assertEqual(order.fund_status, 'HELD')
        self.assertEqual(order.commission_earned, Decimal('100.00'))  # 50 * 2
        wallet = DistributorWallet.objects.get(distributor=self.profile)
        self.assertEqual(wallet.balance, Decimal('0.00'))
        self.assertFalse(
            WalletTransaction.objects.filter(order=order, transaction_type='CREDIT').exists())

        # 4. Customer confirms delivery -> status becomes 'delivered'.
        resp = client.post(f'/api/shop/orders/{order.id}/confirm_delivery/', {}, format='json')
        self.assertEqual(resp.status_code, 200, resp.json())
        order.refresh_from_db()
        self.assertEqual(order.status, 'delivered')

        # 5. A staff user (admin) releases the held funds.
        staff = User.objects.create_user(
            email='admin@ccke.com', password='pass1234', role='ADMIN',
            school=self.school, is_staff=True)
        staff_client = self._api(staff)
        resp = staff_client.post(f'/api/shop/orders/{order.id}/release_funds/', {}, format='json')
        self.assertEqual(resp.status_code, 200, resp.json())
        order.refresh_from_db()
        self.assertEqual(order.fund_status, 'RELEASED')
        self.assertIsNotNone(order.released_at)
        self.assertEqual(order.released_by, staff)
        wallet.refresh_from_db()
        self.assertEqual(wallet.balance, Decimal('100.00'))
        self.assertEqual(wallet.total_earned, Decimal('100.00'))
        self.assertTrue(
            WalletTransaction.objects.filter(order=order, transaction_type='CREDIT', amount=100).exists())

    def test_fee_balance_payment_holds_funds(self):
        client = self._api(self.parent)
        resp = client.post('/api/shop/orders/', {
            'learner': self.learner.id,
            'items': [{'product': self.product.id, 'quantity': 1}],
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        order = Order.objects.get()
        # Pay via fee balance -> confirmed immediately -> funds are HELD (no wallet credit yet)
        resp = client.post(f'/api/shop/orders/{order.id}/pay_fee_balance/', {}, format='json')
        self.assertEqual(resp.status_code, 200, resp.json())
        order.refresh_from_db()
        self.assertEqual(order.fund_status, 'HELD')
        self.assertEqual(order.commission_earned, Decimal('50.00'))
        wallet = DistributorWallet.objects.get(distributor=self.profile)
        self.assertEqual(wallet.balance, Decimal('0.00'))
