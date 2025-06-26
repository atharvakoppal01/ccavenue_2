import frappe
from frappe.model.document import Document

class CCavenueSettings(Document):
    def validate(self):
        if self.is_enabled:
            if not self.merchant_id or not self.access_code or not self.working_key:
                frappe.throw("Merchant ID, Access Code and Working Key are required when CCAvenue is enabled")
        
        # Validate supported currencies
        if self.supported_currencies:
            currencies = [c.strip() for c in self.supported_currencies.split(',')]
            for currency in currencies:
                if len(currency) != 3:
                    frappe.throw(f"Invalid currency code: {currency}. Currency codes must be 3 characters long.")