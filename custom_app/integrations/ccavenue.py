import frappe
import hashlib
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import binascii
import urllib.parse
from frappe import _
from frappe.utils import flt, get_url

class CCavenueIntegration:
    def __init__(self):
        self.settings = frappe.get_single("CCavenue Settings")
        if not self.settings.is_enabled:
            frappe.throw(_("CCAvenue payment gateway is not enabled"))
        
        self.merchant_id = self.settings.merchant_id
        self.access_code = self.settings.access_code
        self.working_key = self.settings.working_key
        self.test_mode = self.settings.test_mode
        
        if self.test_mode:
            self.base_url = "https://test.ccavenue.com/transaction/transaction.do"
        else:
            self.base_url = "https://secure.ccavenue.com/transaction/transaction.do"

    def encrypt(self, plainText, workingKey):
        """Encrypt data using AES encryption"""
        try:
            iv = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f'
            plainText = pad(plainText.encode('utf-8'), AES.block_size)
            encobj = AES.new(workingKey.encode('utf-8'), AES.MODE_CBC, iv)
            encryptedText = encobj.encrypt(plainText)
            return binascii.hexlify(encryptedText).decode('utf-8')
        except Exception as e:
            frappe.log_error(f"CCAvenue encryption error: {str(e)}")
            frappe.throw(_("Encryption failed"))

    def decrypt(self, cipherText, workingKey):
        """Decrypt data using AES decryption"""
        try:
            iv = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f'
            encryptedText = binascii.unhexlify(cipherText)
            decobj = AES.new(workingKey.encode('utf-8'), AES.MODE_CBC, iv)
            decryptedText = decobj.decrypt(encryptedText)
            return unpad(decryptedText, AES.block_size).decode('utf-8')
        except Exception as e:
            frappe.log_error(f"CCAvenue decryption error: {str(e)}")
            return None

    def create_payment_request(self, data):
        """Create payment request for CCAvenue"""
        order_id = data.get("order_id")
        amount = str(flt(data.get("amount"), 2))
        currency = data.get("currency", self.settings.currency)
        
        # Get base URL
        base_url = get_url()
        
        # Use custom URLs if set, otherwise use defaults
        redirect_url = self.settings.success_url or f"{base_url}/api/method/custom_app.api.payment.ccavenue_callback"
        cancel_url = self.settings.cancel_url or f"{base_url}/api/method/custom_app.api.payment.ccavenue_cancel"
        
        # Prepare merchant data
        merchant_data = f"merchant_id={self.merchant_id}&order_id={order_id}&amount={amount}&currency={currency}&redirect_url={redirect_url}&cancel_url={cancel_url}&language=EN"
        
        # Add customer details if available
        customer_fields = [
            'billing_name', 'billing_email', 'billing_tel', 'billing_address',
            'billing_city', 'billing_state', 'billing_zip', 'billing_country',
            'delivery_name', 'delivery_address', 'delivery_city', 'delivery_state',
            'delivery_zip', 'delivery_country', 'delivery_tel'
        ]
        
        for field in customer_fields:
            if data.get(field):
                merchant_data += f"&{field}={urllib.parse.quote(str(data.get(field)))}"
        
        # Encrypt merchant data
        encrypted_data = self.encrypt(merchant_data, self.working_key)
        
        return {
            "payment_url": self.base_url,
            "access_code": self.access_code,
            "encRequest": encrypted_data,
            "merchant_data": merchant_data  # For debugging (remove in production)
        }

    def verify_payment(self, encrypted_response):
        """Verify payment response from CCAvenue"""
        try:
            decrypted_data = self.decrypt(encrypted_response, self.working_key)
            if not decrypted_data:
                return None
                
            response_dict = {}
            for item in decrypted_data.split('&'):
                if '=' in item:
                    key, value = item.split('=', 1)
                    response_dict[key] = urllib.parse.unquote(value)
            
            return response_dict
        except Exception as e:
            frappe.log_error(f"CCAvenue payment verification error: {str(e)}")
            return None

@frappe.whitelist()
def test_connection():
    """Test CCAvenue connection"""
    try:
        settings = frappe.get_single("CCavenue Settings")
        if not settings.is_enabled:
            return {"success": False, "error": "CCAvenue is not enabled"}
        
        if not all([settings.merchant_id, settings.access_code, settings.working_key]):
            return {"success": False, "error": "Missing required credentials"}
        
        # Basic validation - in real scenario you might want to make a test API call
        return {"success": True, "message": "Configuration appears valid"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}