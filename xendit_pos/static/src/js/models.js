odoo.define('xendit_pos.models', function (require) {
    var models = require('point_of_sale.models');
    var PaymentAdyen = require('xendit_pos.payment');
    
    models.register_payment_method('xendit_pos', PaymentAdyen);
    models.load_fields(
        'pos.payment.method', 
        [
            'xendit_pos_terminal_identifier',
            'xendit_pos_test_mode', 
            'xendit_pos_secret_key'
        ]
    );
});
    