from datetime import date

from rest_framework.test import APIClient, APITestCase

from accounts.models import User
from academics.models import Grade, Stream
from procurement.models import Asset, GoodsReceived, PurchaseOrder, PurchaseOrderItem, StockItem, Supplier
from tenants.models import School


def make_school(code):
    return School.objects.create(
        name=f'School {code}', code=code, address='A', phone='1', email=f'{code}@school.com', website='https://school.com',
    )


def make_user(email, role, school):
    return User.objects.create_user(email=email, password='Password123!', role=role, school=school, first_name='T', last_name='User')


class ProcurementRBACTests(APITestCase):
    def setUp(self):
        self.school = make_school('P')
        self.admin = make_user('admin@p.com', 'ADMIN', self.school)
        self.other_school = make_school('Q')
        self.teacher = make_user('t@q.com', 'TEACHER', self.other_school)
        self.supplier = Supplier.objects.create(
            school=self.school, name='Books R Us', contact_person='Jane', email='j@b.com', phone='123',
        )

    def test_unauthenticated_returns_401(self):
        client = APIClient()
        resp = client.get('/api/procurement/suppliers/')
        self.assertEqual(resp.status_code, 401)

    def test_tenant_isolation(self):
        self.client.force_authenticate(user=self.teacher)
        resp = self.client.get('/api/procurement/suppliers/')
        self.assertEqual(resp.status_code, 200)
        names = [s['name'] for s in resp.json()]
        self.assertNotIn('Books R Us', names)

    def test_admin_can_create_supplier(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post(
            '/api/procurement/suppliers/',
            {'name': 'New Supplier', 'contact_person': 'Bob', 'email': 'b@s.com', 'phone': '999'},
            format='json',
        )
        self.assertEqual(resp.status_code, 201, resp.json())
        self.assertTrue(Supplier.objects.filter(name='New Supplier', school=self.school).exists())

    def test_student_cannot_create_supplier(self):
        student = make_user('s@p.com', 'STUDENT', self.school)
        self.client.force_authenticate(user=student)
        resp = self.client.post(
            '/api/procurement/suppliers/',
            {'name': 'Hack Supplier'}, format='json',
        )
        self.assertEqual(resp.status_code, 403)

    def test_purchase_order_approval_workflow(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post(
            '/api/procurement/purchase-orders/',
            {
                'supplier': self.supplier.id,
                'purpose': 'Textbooks for Grade 1',
                'items': [
                    {'description': 'Mathematics textbook', 'quantity': 30, 'unit_price': 500},
                ],
            },
            format='json',
        )
        self.assertEqual(resp.status_code, 201, resp.json())
        po_id = resp.json()['id']

        po = PurchaseOrder.objects.get(id=po_id)
        self.assertEqual(po.status, 'DRAFT')

        resp = self.client.post(f'/api/procurement/purchase-orders/{po_id}/approve/')
        self.assertEqual(resp.status_code, 200, resp.json())
        po.refresh_from_db()
        self.assertEqual(po.status, 'APPROVED')
        self.assertEqual(po.approved_by, self.admin)
        self.assertEqual(len(po.approval_chain), 1)

        resp = self.client.post(f'/api/procurement/purchase-orders/{po_id}/reject/')
        self.assertEqual(resp.status_code, 400)

    def test_receive_updates_stock(self):
        self.client.force_authenticate(user=self.admin)
        po = PurchaseOrder.objects.create(supplier=self.supplier, school=self.school, purpose='Notebooks')
        po.status = 'APPROVED'
        po.save()
        PurchaseOrderItem.objects.create(
            purchase_order=po, description='Exercise Book',
            quantity=50, unit_price=20,
        )
        po.total_amount = 1000
        po.save()

        resp = self.client.post(f'/api/procurement/purchase-orders/{po.id}/receive/')
        self.assertEqual(resp.status_code, 200, resp.json())
        po.refresh_from_db()
        self.assertEqual(po.status, 'RECEIVED')
        stock = StockItem.objects.get(school=self.school, name='Exercise Book')
        self.assertEqual(stock.quantity_in_stock, 50)

    def test_asset_tag_auto_generated(self):
        self.client.force_authenticate(user=self.admin)
        grade = Grade.objects.create(name='G1', stage='primary', order=1)
        Asset.objects.create(
            school=self.school, name='Projector', purchase_cost=50000,
            purchase_date=date.today(),
        )
        asset = Asset.objects.get(name='Projector')
        self.assertTrue(asset.tag.startswith('AST-'))
