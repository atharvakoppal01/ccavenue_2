import frappe
from frappe import _
from frappe.utils import get_url

def get_payment_url(**kwargs):
    """
    This function will be called by ERPNext webshop
    Returns the payment URL for CCAvenue
    """
    try:
        order_id = kwargs.get("order_id")
        if not order_id:
            frappe.throw(_("Order ID is required"))
            
        return f"{get_url()}/api/method/custom_app.api.payment.initiate_ccavenue_payment?order_id={order_id}"
    except Exception as e:
        frappe.log_error(f"CCAvenue payment URL generation error: {str(e)}")
        return None

def is_payment_gateway_enabled():
    """Check if CCAvenue payment gateway is enabled"""
    try:
        settings = frappe.get_single("CCavenue Settings")
        return settings.is_enabled
    except:
        return False

def validate_transaction_currency(currency):
    """
    Validate if the currency is supported by CCAvenue.
    """
    supported_currencies = ["INR", "USD", "EUR"]  # Update with your actual supported currencies

    # Debugging: Log the currency being validated
    frappe.logger().info(f"Validating currency: {currency}")

    if currency not in supported_currencies:
        frappe.logger().error(f"Unsupported currency: {currency}")
        frappe.throw(_("CCAvenue does not support transactions in the currency: {0}").format(currency))

    # Debugging: Log successful validation
    frappe.logger().info(f"Currency {currency} is supported.")
