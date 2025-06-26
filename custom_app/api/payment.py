import frappe
from frappe import _
import json
from custom_app.integrations.ccavenue import CCavenueIntegration
from frappe.utils import get_url, today, now

@frappe.whitelist(allow_guest=True)
def initiate_ccavenue_payment():
    """Initiate CCAvenue payment"""
    try:
        # Get form data
        order_id = frappe.form_dict.get('order_id')
        
        if not order_id:
            frappe.throw(_("Order ID is required"))
        
        # Get sales order
        so = frappe.get_doc("Sales Order", order_id)
        
        # Check if order exists and is valid
        if so.docstatus != 1:
            frappe.throw(_("Sales Order is not submitted"))
        
        # Initialize CCAvenue
        ccavenue = CCavenueIntegration()
        
        # Get customer details
        customer = frappe.get_doc("Customer", so.customer)
        
        # Prepare payment data
        payment_data = {
            "order_id": so.name,
            "amount": so.grand_total,
            "currency": so.currency or "INR",
            "billing_name": so.customer_name or customer.customer_name,
        }
        
        # Add contact details if available
        if so.contact_email:
            payment_data["billing_email"] = so.contact_email
        if so.contact_mobile:
            payment_data["billing_tel"] = so.contact_mobile
        
        # Add billing address if available
        if so.customer_address:
            try:
                address = frappe.get_doc("Address", so.customer_address)
                payment_data.update({
                    "billing_address": address.address_line1 or "",
                    "billing_city": address.city or "",
                    "billing_state": address.state or "",
                    "billing_zip": address.pincode or "",
                    "billing_country": address.country or "India"
                })
            except:
                pass  # Address not found, continue without it
        
        # Add shipping address if different
        if so.shipping_address_name and so.shipping_address_name != so.customer_address:
            try:
                ship_address = frappe.get_doc("Address", so.shipping_address_name)
                payment_data.update({
                    "delivery_name": so.customer_name,
                    "delivery_address": ship_address.address_line1 or "",
                    "delivery_city": ship_address.city or "",
                    "delivery_state": ship_address.state or "",
                    "delivery_zip": ship_address.pincode or "",
                    "delivery_country": ship_address.country or "India"
                })
            except:
                pass  # Shipping address not found
        
        # Create payment request
        payment_request = ccavenue.create_payment_request(payment_data)
        
        # Create Payment Request record for tracking
        pr = frappe.new_doc("Payment Request")
        pr.dt = "Sales Order"
        pr.dn = so.name
        pr.recipient = so.contact_email or customer.email_id
        pr.subject = f"Payment Request for {so.name}"
        pr.message = f"Payment request for order {so.name}"
        pr.payment_gateway = "CCAvenue"
        pr.payment_url = payment_request.get('payment_url')
        pr.payment_account = frappe.db.get_value("Payment Gateway Account", 
                                               {"payment_gateway": "CCAvenue"}, "name")
        pr.currency = so.currency
        pr.grand_total = so.grand_total
        pr.insert(ignore_permissions=True)
        
        # Return HTML form for auto-submission
        html_form = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Redirecting to CCAvenue...</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    text-align: center; 
                    padding: 50px;
                    background-color: #f5f5f5;
                }}
                .container {{ 
                    background: white; 
                    padding: 30px; 
                    border-radius: 10px; 
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    max-width: 500px;
                    margin: 0 auto;
                }}
                .loading {{
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #3498db;
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    animation: spin 2s linear infinite;
                    margin: 20px auto;
                }}
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
                .btn {{ 
                    background-color: #007bff; 
                    color: white; 
                    border: none; 
                    padding: 10px 20px; 
                    border-radius: 5px; 
                    cursor: pointer; 
                    font-size: 16px;
                }}
                .btn:hover {{ background-color: #0056b3; }}
            </style>
        </head>
        <body onload="document.forms[0].submit();">
            <div class="container">
                <h2>Processing Payment</h2>
                <div class="loading"></div>
                <p>Please wait while you are being redirected to CCAvenue payment gateway...</p>
                <form method="post" action="{payment_request['payment_url']}">
                    <input type="hidden" name="encRequest" value="{payment_request['encRequest']}">
                    <input type="hidden" name="access_code" value="{payment_request['access_code']}">
                    <input type="submit" value="Continue to Payment" class="btn">
                </form>
                <p><small>Order ID: {so.name}</small></p>
            </div>
        </body>
        </html>
        '''
        
        frappe.response.type = "page"
        frappe.response.page_name = "payment_redirect.html"
        frappe.response.content = html_form
        
    except Exception as e:
        frappe.log_error(f"CCAvenue payment initiation error: {str(e)}")
        frappe.throw(_("Payment initiation failed. Please try again."))

@frappe.whitelist(allow_guest=True)
def ccavenue_callback():
    """Handle CCAvenue payment callback"""
    try:
        # Get encrypted response
        enc_response = frappe.form_dict.get('encResp')
        
        if not enc_response:
            frappe.throw(_("Invalid payment response"))
        
        # Initialize CCAvenue
        ccavenue = CCavenueIntegration()
        
        # Decrypt and verify response
        response_data = ccavenue.verify_payment(enc_response)
        
        if not response_data:
            frappe.throw(_("Payment verification failed"))
        
        order_status = response_data.get('order_status')
        order_id = response_data.get('order_id')
        tracking_id = response_data.get('tracking_id')
        amount = response_data.get('amount')
        
        # Log the transaction
        frappe.log_error(f"CCAvenue Callback: {response_data}", "CCAvenue Payment Response")
        
        if order_status == 'Success':
            # Payment successful - update sales order
            so = frappe.get_doc("Sales Order", order_id)
            
            # Check if payment entry already exists
            existing_pe = frappe.db.exists("Payment Entry", {
                "reference_no": tracking_id,
                "docstatus": 1
            })
            
            if not existing_pe:
                # Create payment entry
                pe = frappe.new_doc("Payment Entry")
                pe.payment_type = "Receive"
                pe.party_type = "Customer"
                pe.party = so.customer
                pe.paid_amount = float(amount)
                pe.received_amount = pe.paid_amount
                pe.reference_no = tracking_id
                pe.reference_date = today()
                pe.mode_of_payment = "CCAvenue"
                pe.posting_date = today()
                
                # Get or create mode of payment
                if not frappe.db.exists("Mode of Payment", "CCAvenue"):
                    mop = frappe.new_doc("Mode of Payment")
                    mop.mode_of_payment = "CCAvenue"
                    mop.type = "Bank"
                    mop.insert(ignore_permissions=True)
                
                # Add reference to sales order
                pe.append("references", {
                    "reference_doctype": "Sales Order",
                    "reference_name": so.name,
                    "allocated_amount": pe.paid_amount
                })
                
                pe.insert(ignore_permissions=True)
                pe.submit()
                
                # Update sales order payment status
                so.db_set("payment_status", "Paid")
                so.add_comment("Comment", f"Payment received via CCAvenue. Transaction ID: {tracking_id}")
            
            # Redirect to success page
            frappe.local.response.location = f"{get_url()}/payment-success?order_id={order_id}&tracking_id={tracking_id}"
            frappe.local.response.type = "redirect"
            
        else:
            # Payment failed
            failure_message = response_data.get('failure_message', 'Payment failed')
            frappe.local.response.location = f"{get_url()}/payment-failed?order_id={order_id}&reason={failure_message}"
            frappe.local.response.type = "redirect"
            
    except Exception as e:
        frappe.log_error(f"CCAvenue callback error: {str(e)}")
        frappe.local.response.location = f"{get_url()}/payment-failed?reason=Payment processing error"
        frappe.local.response.type = "redirect"

@frappe.whitelist(allow_guest=True)
def ccavenue_cancel():
    """Handle CCAvenue payment cancellation"""
    order_id = frappe.form_dict.get('order_id', '')
    frappe.local.response.location = f"{get_url()}/payment-cancelled?order_id={order_id}"
    frappe.local.response.type = "redirect"