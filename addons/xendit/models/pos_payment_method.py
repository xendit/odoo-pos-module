# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json
import logging
from pprint import pprint
import random
import requests
import string

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

from odoo.http import request

_logger = logging.getLogger(__name__)

class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    def _get_payment_terminal_selection(self):
        return super(PosPaymentMethod, self)._get_payment_terminal_selection() + [('xendit', 'Xendit')]

    xendit_secret_key = fields.Char(string="Xendit Secret Key", help='Enter your xendit secret key.', copy=False)
    xendit_terminal_identifier = fields.Char(help='[Terminal model]-[Serial number], for example: P400Plus-123456789', copy=False)
    xendit_test_mode = fields.Boolean(help='Run transactions in the test environment.')
    xendit_latest_response = fields.Char(help='Technical field used to buffer the latest asynchronous notification from Xendit.', copy=False, groups='base.group_erp_manager')
    xendit_latest_diagnosis = fields.Char(help='Technical field used to determine if the terminal is still connected.', copy=False, groups='base.group_erp_manager')

    @api.constrains('xendit_terminal_identifier')
    def _check_xendit_terminal_identifier(self):
        for payment_method in self:
            if not payment_method.xendit_terminal_identifier:
                continue
            existing_payment_method = self.search([('id', '!=', payment_method.id),
                                                   ('xendit_terminal_identifier', '=', payment_method.xendit_terminal_identifier)],
                                                  limit=1)
            if existing_payment_method:
                raise ValidationError(_('Terminal %s is already used on payment method %s.')
                                      % (payment_method.xendit_terminal_identifier, existing_payment_method.display_name))

    def _is_write_forbidden(self, fields):
        whitelisted_fields = set(('xendit_latest_response', 'xendit_latest_diagnosis'))
        return super(PosPaymentMethod, self)._is_write_forbidden(fields - whitelisted_fields)

    @api.model
    def get_latest_xendit_status(self, data):
        '''See the description of proxy_xendit_request as to why this is an
        @api.model function.
        '''
        print('\n --- Xendit get_latest_xendit_status ----')
        pprint(data)
                
        # Poll the status of the terminal if there's no new
        # notification we received. This is done so we can quickly
        # notify the user if the terminal is no longer reachable due
        # to connectivity issues.

        
        #latest_response = json.loads(latest_response) if latest_response else False
        

#        transaction_id = data["transaction_id"]

        # Send status request to the m2_kiosk_app
        url = "https://httpstat.us/200"
#        json_data={"transaction_id": transaction_id, 
#                   "requested_amount": requested_amount}
                                
        r = requests.post(url, json.dumps(data))

        #result = check_payment_local_node('testnet', transaction_id, wallet_id, requested_amount)
        result = "no_pay"

        #payment_method = self.sudo().browse(payment_method_id)
        payment_method = request.env['pos.payment.method'].sudo().search([('use_payment_terminal', '=', 'xendit')], limit=1)
        
        latest_response = payment_method.xendit_latest_response
        print("\n Paypad latest_response : " + repr(latest_response))
        json_result = json.loads(latest_response)
        payment_method.xendit_latest_response = ''  # avoid handling old responses multiple times
        
        result = json_result["payment_status"]

        return { 'response': result }

    @api.model
    def request_payment(self, data):
        '''Necessary because Xendit's endpoints don't have CORS enabled. This is an
        @api.model function to avoid concurrent update errors. Xendit's
        async endpoint can still take well over a second to complete a
        request. By using @api.model and passing in all data we need from
        the POS we avoid locking the pos_payment_method table. This way we
        avoid concurrent update errors when Xendit calls us back on
        /xendit/notification which will need to write on
        pos.payment.method.
        '''
        print('--- Xendit request_payment 2 ----')
        pprint(data)

        #transaction_id = data["transaction_id"]
        #requested_amount = data["requested_amount"]

        # Send payment request to the Xendit TPI
        # url = "https://httpstat.us/200"
        #json_data={"transaction_id": transaction_id,                  
        #           "requested_amount": requested_amount}
 
        # r = requests.post(url, json.dumps(data))

        return True

    @api.onchange('use_payment_terminal')
    def _onchange_use_payment_terminal(self):
        super(PosPaymentMethod, self)._onchange_use_payment_terminal()
        if self.use_payment_terminal != 'xendit':
            self.xendit_secret_key = False
            self.xendit_terminal_identifier = False
