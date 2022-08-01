odoo.define('xendit.models', function (require) {
    var models = require('point_of_sale.models');
    var PaymentAdyen = require('xendit.payment');
    
    models.register_payment_method('xendit', PaymentAdyen);
    models.load_fields('pos.payment.method', ['xendit_terminal_identifier', 'xendit_test_mode', 'xendit_secret_key']);
    });
    