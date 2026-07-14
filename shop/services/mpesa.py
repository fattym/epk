import requests
from django.conf import settings
from django.utils import timezone
from .models import Payment


class MpesaDaraja:
    """Safaricom Daraja API integration for STK Push"""
    
    def __init__(self):
        self.consumer_key = getattr(settings, 'MPESA_CONSUMER_KEY', '')
        self.consumer_secret = getattr(settings, 'MPESA_CONSUMER_SECRET', '')
        self.business_shortcode = getattr(settings, 'MPESA_BUSINESS_SHORTCODE', '')
        self.passkey = getattr(settings, 'MPESA_PASSKEY', '')
        self.callback_url = getattr(settings, 'MPESA_CALLBACK_URL', '')
        self.environment = getattr(settings, 'MPESA_ENVIRONMENT', 'sandbox')
        
        if self.environment == 'sandbox':
            self.base_url = 'https://sandbox.safaricom.co.ke'
        else:
            self.base_url = 'https://api.safaricom.co.ke'

    def get_access_token(self):
        """Get OAuth access token from Daraja"""
        try:
            response = requests.get(
                f'{self.base_url}/oauth/v1/generate?grant_type=client_credentials',
                auth=(self.consumer_key, self.consumer_secret),
                timeout=30,
            )
            response.raise_for_status()
            return response.json().get('access_token')
        except Exception as e:
            print(f'M-Pesa auth error: {e}')
            return None

    def initiate_stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """Initiate STK Push - prompts customer to enter PIN on their phone"""
        access_token = self.get_access_token()
        if not access_token:
            return {'success': False, 'error': 'Failed to get access token'}

        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        password = self._generate_password(timestamp)

        payload = {
            'BusinessShortCode': self.business_shortcode,
            'Password': password,
            'Timestamp': timestamp,
            'TransactionType': 'CustomerPayBillOnline',
            'Amount': int(amount),
            'PartyA': phone_number,
            'PartyB': self.business_shortcode,
            'PhoneNumber': phone_number,
            'CallBackURL': self.callback_url,
            'AccountReference': account_reference,
            'TransactionDesc': transaction_desc,
        }

        try:
            response = requests.post(
                f'{self.base_url}/mpesa/stkpush/v1/processrequest',
                headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'},
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return {
                'success': data.get('ResponseCode') == '0',
                'checkout_request_id': data.get('CheckoutRequestID'),
                'merchant_request_id': data.get('MerchantRequestID'),
                'customer_message': data.get('CustomerMessage'),
                'response_code': data.get('ResponseCode'),
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _generate_password(self, timestamp):
        import base64
        data = f'{self.business_shortcode}{self.passkey}{timestamp}'
        return base64.b64encode(data.encode()).decode()

    @staticmethod
    def format_phone_number(phone):
        """Convert 07XXXXXXXXX to 2547XXXXXXXXX"""
        phone = phone.strip().replace(' ', '').replace('+', '')
        if phone.startswith('0'):
            return '254' + phone[1:]
        return phone
