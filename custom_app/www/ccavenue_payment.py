import frappe
from frappe import _
import json
from custom_app.custom_app.integrations.ccavenue import CCavenueIntegration

def get_context(context):
    # This will be called when accessing /ccavenue_payment
    context.no_cache = 1
    
    # Get order details from URL parameters
    order_id = frappe.form_dict.get('order_id')
    if not order_id:
        frappe.throw(_("Order ID is required"))
    
    # Get sales order details
    so = frappe.get_doc("Sales Order", order_id)
    
    context.order = so
    context.payment_url = "/api/method/custom_app.custom_app.api.initiate_ccavenue_payment"
    
    return context
