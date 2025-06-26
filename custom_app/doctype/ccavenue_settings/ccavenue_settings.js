frappe.ui.form.on('CCavenue Settings', {
    refresh: function(frm) {
        if (frm.doc.is_enabled) {
            frm.add_custom_button(__('Test Connection'), function() {
                frappe.call({
                    method: 'custom_app.integrations.ccavenue.test_connection',
                    callback: function(r) {
                        if (r.message.success) {
                            frappe.msgprint(__('Connection test successful!'));
                        } else {
                            frappe.msgprint(__('Connection test failed: ') + r.message.error);
                        }
                    }
                });
            });
        }
        
        // Set default URLs if not set
        if (!frm.doc.success_url) {
            frm.set_value('success_url', window.location.origin + '/payment-success');
        }
        if (!frm.doc.failure_url) {
            frm.set_value('failure_url', window.location.origin + '/payment-failed');
        }
        if (!frm.doc.cancel_url) {
            frm.set_value('cancel_url', window.location.origin + '/payment-cancelled');
        }
    }
});