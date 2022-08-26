odoo.define('xendit_pos.payment', function (require) {
    "use strict";
    
    const core = require('web.core');
    const rpc = require('web.rpc');
    const PaymentInterface = require('point_of_sale.PaymentInterface');
    const { Gui } = require('point_of_sale.Gui');

    const paymentStatus = {
        PENDING: 'pending',
        RETRY: 'retry',
        WAITING: 'waiting',
        FORCE_DONE: 'force_done'
    }

    // For string translations
    const _t = core._t;

    const PaymentXenditPOS = PaymentInterface.extend({
        send_payment_request: function (cid) {
            this._super.apply(this, arguments);
            this._reset_state();
    
            return this._xendit_pay();
        },

        get_selected_payment: function () {
            const paymentLine = this.pos.get_order().selected_paymentline;
            if (paymentLine && paymentLine.payment_method.use_payment_terminal === 'xendit_pos') {
                return paymentLine;
            }
            return false;
        },

        send_payment_cancel: function (order, cid) {
            this._super.apply(this, arguments);
            // set only if we are polling
            this.was_cancelled = !!this.polling;

            // Cancel order on Xendit
            const paymentLine = this.get_selected_payment();
            return this._xendit_cancel(paymentLine);
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

        _xendit_cancel: function (paymentLine) {
            const self = this;

            if (!paymentLine || paymentLine.getXenditInvoiceId() == null) {
                return Promise.resolve();
            }

            const xenditInvoiceId = paymentLine.getXenditInvoiceId();
            rpc.query({
                model: 'pos.payment.method',
                method: 'cancel_payment',
                args: [xenditInvoiceId],
            }, {
                timeout: 10000,
                shadow: true,
            }).catch(
                this._handle_odoo_connection_failure.bind(this)
            );

            return Promise.resolve();
        },

        _xendit_get_sale_id: function () {
            const config = this.pos.config;
            return _.str.sprintf('%s (ID: %s)', config.display_name, config.id);
        },

        _handle_odoo_connection_failure: function (data) {
            // handle timeout
            const paymentLine = this.get_selected_payment();
            if (paymentLine) {
                paymentLine.set_payment_status(paymentStatus.RETRY);
            }

            this._show_error(_('Could not connect to the Odoo server, please check your internet connection and try again.'));
            return Promise.reject(data); // prevent subsequent onFullFilled's from being called
        },

        _xendit_pay: function () {
            const self = this;

            const order = this.pos.get_order();
            const paymentLine = this.get_selected_payment();
            if (paymentLine && paymentLine.amount <= 0) {
                this._show_error(
                    _t("Cannot process transaction with zero or negative amount.")
                );
                return Promise.resolve();
            }

            const receipt_data = order.export_for_printing();
            receipt_data['amount'] = paymentLine.amount;
            
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
            const paymentLine = this.get_selected_payment();

            // If the payment line dont have xendit invoice then stop polling retry.
            if(!paymentLine || paymentLine.getXenditInvoiceId() == null){
                resolve(false);
                return Promise.resolve();
            }

            const data = {
                'sale_id': this._xendit_get_sale_id(),
                'transaction_id': order.uid,
                'wallet_id': this.payment_method.xendit_pos_secret_key,
                'requested_amount': paymentLine.amount,
                "xendit_invoice_id": paymentLine.getXenditInvoiceId()
            };

            return rpc.query({
                model: 'pos.payment.method',
                method: 'get_latest_xendit_pos_status',
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

                if (invoice.id === paymentLine.getXenditInvoiceId()) {
                    self._update_payment_status(invoice, resolve, reject);
                } else {
                    paymentLine.set_payment_status(paymentStatus.RETRY);
                    reject();
                }
            });
        },

        _update_payment_status: function(invoice, resolve, reject) {
            if (invoice.status == 'PAID' || invoice.status == 'SETTLED') {
                $('#xendit-payment-status').text('Paid');
                $("#invoice-link > a").text('Paid');
                resolve(true);
            } else if(invoice.status == 'EXPIRED'){
                $('#xendit-payment-status').text('Expired');
                $("#invoice-link > a").text('Expired');

                const paymentLine = this.get_selected_payment();
                if (paymentLine) {
                    paymentLine.set_payment_status(paymentStatus.RETRY);
                }
                reject();
            }
        },

        _generate_qr_code: function (invoice_url) {
            return '<img src="https://api.qrserver.com/v1/create-qr-code/?data=' + invoice_url + '" '
            + 'alt="" width="180px" height="180px"/>';
        },

        _generate_invoice_link: function (invoice_url) {
            return '<a class="button next highlight" style="float:none;" href="' + invoice_url + '" target="_blank">Pay at Xendit</a>'
        },
    
        _xendit_handle_response: function (response) {
            const self = this;
            const paymentLine = this.get_selected_payment();

            if (response.error) {
                let errorMessage = _t(response.error.message)
                if (response.error.status_code == 401) {
                    errorMessage = _t('Authentication failed. Please check your Xendit credentials.');
                }
                this._show_error(
                    _t('System Error'),
                    errorMessage
                );
                if (paymentLine) {
                    paymentLine.set_payment_status(paymentStatus.FORCE_DONE);
                }
                return Promise.resolve();

             } else if (response.id) {
                
                Gui.showPopup("XenditQRCodePopup", {
                    'title': _t('Scan to pay'),
                    'qrCodeImage': self._generate_qr_code(response.invoice_url),
                    'invoiceLink': self._generate_invoice_link(response.invoice_url),
                });

                if (paymentLine) {
                    paymentLine.setXenditInvoiceId(response.id);
                    paymentLine.set_payment_status(paymentStatus.WAITING);
                }
                return this.start_get_status_polling();
            }
        },

        start_get_status_polling() {
            var self = this;
            var res = new Promise(function (resolve, reject) {
                clearTimeout(self.polling);
                self._poll_for_response(resolve, reject);
                self.polling = setInterval(function () {
                    self._poll_for_response(resolve, reject);
                }, 5500);
            });
    
            // make sure to stop polling when we're done
            res.finally(function () {
                self._reset_state();
            });

            Promise.resolve();
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

    return PaymentXenditPOS;
});