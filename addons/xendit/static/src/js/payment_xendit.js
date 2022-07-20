odoo.define('xendit.payment', function (require) {
    "use strict";
    
    var core = require('web.core');
    var rpc = require('web.rpc');
    var PaymentInterface = require('point_of_sale.PaymentInterface');
    
    // For string translations
    var _t = core._t;
    
    var PaymentXendit = PaymentInterface.extend({
        send_payment_request: function (cid) {
            this._super.apply(this, arguments);
            this._reset_state();
            
            console.log('send_payment_request');
    
            return this._xendit_pay();
        },

        send_payment_cancel: function (order, cid) {
            this._super.apply(this, arguments);
            // set only if we are polling
            this.was_cancelled = !!this.polling;
            return this._xendit_cancel();
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
            console.log('_xendit_cancel')
    
            return Promise.resolve();
        },

        _xendit_get_sale_id: function () {
            var config = this.pos.config;
            return _.str.sprintf('%s (ID: %s)', config.display_name, config.id);
        },

        _handle_odoo_connection_failure: function (data) {
            // handle timeout
            var line = this.pos.get_order().selected_paymentline;
            if (line) {
                line.set_payment_status('retry');
            }
            this._show_error(_('Could not connect to the Odoo server, please check your internet connection and try again.'));
    
            return Promise.reject(data); // prevent subsequent onFullFilled's from being called
        },

        _xendit_pay: function () {
            var self = this;
            console.log('_xendit_pay');

            var order = this.pos.get_order();
            var receipt_data = order.export_for_printing();

            console.log('receipt_data');
            console.log(receipt_data);

            return this._call_xendit(receipt_data).then(function (data) {
                return self._xendit_handle_response(data);
            });
        },

        // Create the payment request 
        _call_xendit: function (data) {
            var self = this;
            
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
            }).catch(this._handle_odoo_connection_failure.bind(this));
        },

        _poll_for_response: function (resolve, reject) {
            var self = this;
            if (this.was_cancelled) {
                resolve(false);
                return Promise.resolve();
            }
            
            console.log('_poll_for_response');
            
            var order = this.pos.get_order();
            var line = order.selected_paymentline;
            
            var data = {'sale_id': this._xendit_get_sale_id(),
                        'transaction_id': order.uid,
                        'wallet_id': this.payment_method.xendit_secret_key,
                        'requested_amount': line.amount,};        
            console.log(data)
            
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
            }).then(function (status) {
                console.log('_poll_for_response -> then');
                console.log(status)
    
                self.remaining_polls = 2;
                
                if (status.response == 'success') {
                    console.log('success');
                    resolve(true);
                //} else {
                //    console.log('not_received');
                //    line.set_payment_status('force_done');
                //    reject();
                    //reject();        
                }
            });
        },
    
        _xendit_handle_response: function (response) {
            var self = this;

            console.log(response, '<<< response 2');
            
            var line = this.pos.get_order().selected_paymentline;
            console.log(line, '<<< line');
            line.set_payment_status('waitingCard');
            // this.pos.chrome.gui.current_screen.render_paymentlines();

            var res = new Promise(function (resolve, reject) {
                var order = self.pos.get_order();
                var line = order.selected_paymentline;
                //line.set_payment_status('waitingCard');
                console.log('start_polling');
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

        _show_error: function (msg, title) {
            if (!title) {
                title =  _t('xendit Error');
            }
            this.pos.gui.show_popup('error',{
                'title': title,
                'body': msg,
            });
        },
    });

    return PaymentXendit;
    });
    