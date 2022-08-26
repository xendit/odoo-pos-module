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
from . import xendit_client

_logger = logging.getLogger(__name__)

class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    def _get_payment_terminal_selection(self):
        return super(PosPaymentMethod, self)._get_payment_terminal_selection() + [('xendit_pos', 'Xendit')]

    xendit_pos_secret_key = fields.Char(string="Xendit Secret Key", required=True, help='Enter your xendit secret key.', copy=False)
    xendit_pos_terminal_identifier = fields.Char(help='[Terminal model]-[Serial number], for example: P400Plus-123456789', copy=False)
    xendit_pos_test_mode = fields.Boolean(help='Run transactions in the test environment.')
    xendit_pos_latest_response = fields.Char(help='Technical field used to buffer the latest asynchronous notification from Xendit.', copy=False, groups='base.group_erp_manager')
    xendit_pos_latest_diagnosis = fields.Char(help='Technical field used to determine if the terminal is still connected.', copy=False, groups='base.group_erp_manager')
    
    xendit_invoice_id = ''
    xenditClient = xendit_client.XenditClient

    @api.constrains('xendit_pos_terminal_identifier')
    def _check_xendit_pos_terminal_identifier(self):
        for payment_method in self:
            if not payment_method.xendit_pos_terminal_identifier:
                continue
            existing_payment_method = self.search([('id', '!=', payment_method.id),
                                                   ('xendit_pos_terminal_identifier', '=', payment_method.xendit_pos_terminal_identifier)],
                                                  limit=1)
            if existing_payment_method:
                raise ValidationError(_('Terminal %s is already used on payment method %s.')
                                      % (payment_method.xendit_pos_terminal_identifier, existing_payment_method.display_name))

    def _is_write_forbidden(self, fields):
        whitelisted_fields = set(('xendit_pos_latest_response', 'xendit_pos_latest_diagnosis'))
        return super(PosPaymentMethod, self)._is_write_forbidden(fields - whitelisted_fields)

    @api.model
    def get_latest_xendit_pos_status(self, data):
        '''See the description of proxy_xendit_pos_request as to why this is an
        @api.model function.
        '''

        # Poll the status of the terminal if there's no new
        # notification we received. This is done so we can quickly
        # notify the user if the terminal is no longer reachable due
        # to connectivity issues.

        payment_method = request.env['pos.payment.method'].sudo().search([('use_payment_terminal', '=', 'xendit_pos')], limit=1)
        payment_method.xendit_pos_latest_response = ''  # avoid handling old responses multiple times

        self.xenditClient._set_odoo_company_id(self.xenditClient, self.env.company.id)
        invoice = self.xenditClient._get_invoice(
            self.xenditClient,
            data["xendit_invoice_id"]
        )
        return { 'response': invoice }

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
        
        self.xenditClient._set_odoo_company_id(self.xenditClient, self.env.company.id)
        invoice = self.xenditClient._create_invoice(
            self.xenditClient,
            json.loads(json.dumps(data))           
        )
        return invoice

    @api.model
    def cancel_payment(self, xenditInvoiceId):
        self.xenditClient._set_odoo_company_id(self.xenditClient, self.env.company.id)
        res = self.xenditClient._cancel_invoice(
            self.xenditClient,
            xenditInvoiceId
        )
        return res

    @api.onchange('use_payment_terminal')
    def _onchange_use_payment_terminal(self):
        super(PosPaymentMethod, self)._onchange_use_payment_terminal()
        if self.use_payment_terminal != 'xendit_pos':
            self.xendit_pos_secret_key = False
            self.xendit_pos_terminal_identifier = False