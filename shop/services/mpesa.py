import requests
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from shop.models import Payment


class ChamaGoIntegrator:
    """ChamaGO Integrator API integration for M-Pesa STK Push via virtual wallets.

    Flow:
      1. get_token()  → authenticate with api_key, cache Bearer token (1h ttl)
      2. create_wallet() → create a virtual sub-account, get account_number
      3. initiate_stk_push() → dispatch STK prompt to the customer's phone
    """

    def __init__(self):
        self.api_key = getattr(settings, 'CHAMAGO_API_KEY', '')
        base = getattr(settings, 'CHAMAGO_API_URL', 'https://api.chamago.co.ke')
        self.base_url = base.rstrip('/')
        self._token = None
        self._token_expires_at = None

    def get_token(self):
        """Exchange api_key for a short-lived Bearer token."""
        if self._token and self._token_expires_at and timezone.now() < self._token_expires_at:
            return self._token
        try:
            response = requests.post(
                f'{self.base_url}/api/apps/token',
                headers={'Content-Type': 'application/json'},
                json={'api_key': self.api_key},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            if data.get('status') and data.get('token'):
                self._token = data['token']
                self._token_expires_at = timezone.now() + timedelta(seconds=data.get('expires_in', 3600) - 60)
                return self._token
            return None
        except Exception as e:
            print(f'ChamaGO auth error: {e}')
            return None

    def _auth_headers(self):
        token = self.get_token()
        if not token:
            return None
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }

    def create_wallet(self, holder_name, name=None):
        """Create a virtual wallet for a customer. Returns dict with account_number."""
        headers = self._auth_headers()
        if not headers:
            return {'success': False, 'error': 'Failed to get access token'}
        if not name:
            name = f'{holder_name} - Wallet'
        try:
            response = requests.post(
                f'{self.base_url}/api/apps/wallets',
                headers=headers,
                json={'holder_name': holder_name, 'name': name},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            wallet_data = data.get('data', {}) if data.get('status') else {}
            return {
                'success': data.get('status', False),
                'account_number': wallet_data.get('account_number'),
                'wallet_name': wallet_data.get('name'),
                'holder_name': wallet_data.get('holder_name'),
                'message': data.get('message', ''),
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def initiate_stk_push(self, phone_number, amount, wallet=None, channel_code='MPESA'):
        """Send an STK Push prompt to the customer's phone.

        Returns dict with ``success``, ``checkout_request_id`` (ChamaGO transaction_id),
        and ``message``.
        """
        headers = self._auth_headers()
        if not headers:
            return {'success': False, 'error': 'Failed to get access token'}

        payload = {
            'mobile': phone_number,
            'amount': int(amount),
            'channel_code': channel_code,
        }
        if wallet is not None:
            payload['wallet'] = wallet

        try:
            response = requests.post(
                f'{self.base_url}/api/apps/topup',
                headers=headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            resp_data = data.get('data', {}) if data.get('status') else {}
            checkout_request_id = resp_data.get('transaction_id') or resp_data.get('checkout_request_id') or ''
            return {
                'success': data.get('status', False),
                'checkout_request_id': checkout_request_id,
                'message': data.get('message', ''),
                'data': resp_data,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def format_phone_number(phone):
        """Convert 07XXXXXXXXX to 2547XXXXXXXXX"""
        phone = phone.strip().replace(' ', '').replace('+', '')
        if phone.startswith('0'):
            return '254' + phone[1:]
        return phone
