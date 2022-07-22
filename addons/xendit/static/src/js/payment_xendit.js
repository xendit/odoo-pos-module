odoo.define('xendit.payment', function (require) {
    "use strict";
    
    const core = require('web.core');
    const rpc = require('web.rpc');
    const PaymentInterface = require('point_of_sale.PaymentInterface');
    const { Gui } = require('point_of_sale.Gui');

    // For string translations
    const _t = core._t;
    const xendit_invoice_id = '';

    const PaymentXendit = PaymentInterface.extend({
        send_payment_request: function (cid) {
            this._super.apply(this, arguments);
            this._reset_state();
    
            return this._xendit_pay();
        },

        send_payment_cancel: function (order, cid) {
            this._super.apply(this, arguments);
            // set only if we are polling
            this.was_cancelled = !!this.polling;
            return this._xendit_cancel();
        },

        set_xendit_invoice_id: function(id){
            this.xendit_invoice_id = id;
            return this;
        },

        close: function () {
            this._super.apply(this, arguments);
        },

        // private methods
        _reset_state: function () {
            this.was_cancelled = false;
            this.last_diagnosis_service_id = false;
            this.remaining_polls = 2;
            clearTimeout(this.polling);
        },

        _xendit_cancel: function (ignore_error) {
            return Promise.resolve();
        },

        _xendit_get_sale_id: function () {
            const config = this.pos.config;
            return _.str.sprintf('%s (ID: %s)', config.display_name, config.id);
        },

        _handle_odoo_connection_failure: function (data) {
            // handle timeout
            const line = this.pos.get_order().selected_paymentline;
            if (line) {
                line.set_payment_status('retry');
            }
            this._show_error(_('Could not connect to the Odoo server, please check your internet connection and try again.'));
            return Promise.reject(data); // prevent subsequent onFullFilled's from being called
        },

        _xendit_pay: function () {
            const self = this;

            const order = this.pos.get_order();
            const receipt_data = order.export_for_printing();
            return this._call_xendit(receipt_data).then(function (data) {
                return self._xendit_handle_response(data);
            });
        },

        // Create the payment request 
        _call_xendit: function (data) {
            const self = this;
            
            return rpc.query({
                model: 'pos.payment.method',
                method: 'request_payment',
                args: [data],
            }, {
                // When a payment terminal is disconnected it takes Adyen
                // a while to return an error (~6s). So wait 10 seconds
                // before concluding Odoo is unreachable.
                timeout: 10000,
                shadow: true,
            }).catch(
                this._handle_odoo_connection_failure.bind(this)
            );
        },

        _poll_for_response: function (resolve, reject) {
            const self = this;
            if (this.was_cancelled) {
                resolve(false);
                return Promise.resolve();
            }

            const order = this.pos.get_order();
            const line = order.selected_paymentline;

            const data = {
                'sale_id': this._xendit_get_sale_id(),
                'transaction_id': order.uid,
                'wallet_id': this.payment_method.xendit_secret_key,
                'requested_amount': line.amount,
                "xendit_invoice_id": self.xendit_invoice_id
            };

            console.log(data);

            return rpc.query({
                model: 'pos.payment.method',
                method: 'get_latest_xendit_status',
                args: [data],
            }, {
                timeout: 5000,
                shadow: true,
            }).catch(function (data) {
                reject();
                return self._handle_odoo_connection_failure(data);
            }).then(function (result) {
                self.remaining_polls = 2;
                const invoice = result.response;

                if (invoice.status == 'PAID' || invoice.status == 'SETTLE') {
                    $('#xendit-payment-status').text('Paid');
                    resolve(true);
                } else if(invoice.status == 'EXPIRED'){
                    $('#xendit-payment-status').text('Expired');
                   line.set_payment_status('force_done');
                   reject();
                }
            });
        },

        _generate_qr_code: function (invoice_url) {
            return '<img src="https://api.qrserver.com/v1/create-qr-code/?data=' + invoice_url + '" '
            + 'alt="" width="180px" height="180px"/>';
        },
    
        _xendit_handle_response: function (response) {
            const self = this;
            const line = this.pos.get_order().selected_paymentline;

            if (response.error) {
                let errorMessage = _t(response.error.message)
                if(response.error.status_code == 401){
                    errorMessage = _t('Authentication failed. Please check your Xendit credentials.');
                }
                this._show_error(
                    _t('System Error'),
                    errorMessage
                );
                line.set_payment_status('force_done');
                return Promise.resolve();
            }

            if(response.id){
                Gui.showPopup("XenditQRCodePopup", {
                    'title': _t('Scan to pay'),
                    'qrCodeImage': self._generate_qr_code(response.invoice_url),
                    'shortInvoiceUrl': response.short_invoice_url,
                });

                self.set_xendit_invoice_id(response.id);
            }

            line.set_payment_status('waitingCard');
            // this.pos.chrome.gui.current_screen.render_paymentlines();

            const res = new Promise(function (resolve, reject) {
                const order = self.pos.get_order();
                const line = order.selected_paymentline;
                //line.set_payment_status('waitingCard');
                clearTimeout(self.polling);

                self.polling = setInterval(function () {
                    self._poll_for_response(resolve, reject);
                }, 5000);
            });

            // make sure to stop polling when we're done
            res.finally(function () {
                self._reset_state();
            });
            
            return res;    
        },

        _show_error: function (title, msg) {
            if (!title) {
                title =  _t('xendit Error');
            }
            Gui.showPopup("ErrorPopup", {
                'title': title,
                'body': msg,
            });
        },
    });

    return PaymentXendit;
    });
    