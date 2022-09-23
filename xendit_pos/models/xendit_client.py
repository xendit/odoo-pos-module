# -*- coding: utf-8 -*-
from ast import In
import secrets
import this
from wsgiref import headers
import json
import requests
import base64

from odoo.http import request
from odoo import models, fields
from . import data_utils,  error_handler, encrypt

class XenditClient():

    plugin_name = 'ODOO_POS'
    plugin_version = '1.0'

    tpi_server_url = "https://tpi.xendit.co"

    dataUtils = data_utils.DataUtils()
    errorHandler = error_handler.ErrorHandler()

    def get_xendit_secret_key(self, payment_method):
        if payment_method.xendit_encrypt_key is False:
            return payment_method.xendit_pos_secret_key

        return encrypt.decrypt(payment_method.xendit_pos_secret_key, payment_method.xendit_encrypt_key)

    def generate_header(self, payment_method):
        return self.dataUtils.generateHeader(
            self.get_xendit_secret_key(self, payment_method),
            self.plugin_name,
            self.plugin_version
        )

    def generate_payload(self, data):
        customerObject = self.dataUtils.generateInvoiceCustomer(data['client'])
        payload = {
            'external_id': data['name'].split(' ')[1],
            'amount': data['amount'],
            'currency': data['currency']['name'],
            'description': data['name'],
            'items': self.dataUtils.generateInvoiceItems(data),
            'customer': customerObject,
            'client_type': 'INTEGRATION',
        }

        if len(customerObject) > 0 and not self.dataUtils.isEmptyString(customerObject['email']):
            payload['payer_email'] = customerObject['email']

        return payload

    def create_invoice(self, payment_method, data):
        endpoint = self.tpi_server_url + '/payment/xendit/invoice'
        headers = self.generate_header(self, payment_method)
        payload = self.generate_payload(self, data)

        try:
            res = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        except requests.exceptions.RequestException as err:
            return self.errorHandler.handleError('create_invoice', err)

        response = json.loads(res.text)

        # If error
        if res.status_code != 200:
            return self.errorHandler.handleError(
                'create_invoice',
                response["message"],
                res.status_code
            )

        return response

    def get_invoice(self, payment_method, invoice_id):
        endpoint = self.tpi_server_url + '/payment/xendit/invoice/' + invoice_id
        headers = self.generate_header(self, payment_method)

        try:
            res = requests.get(endpoint, headers=headers, timeout=10)
        except requests.exceptions.RequestException as err:
            return self.errorHandler.handleError('get_invoice', err)

        response = json.loads(res.text)

        # If error
        if res.status_code != 200:
            return self.errorHandler.handleError(
                'get_invoice',
                response["message"],
                res.status_code
            )

        return response

    def cancel_invoice(self, payment_method, invoice_id):
        endpoint = self.tpi_server_url + '/payment/xendit/invoice/' + invoice_id + '/expire'
        headers = self.generate_header(self, payment_method)

        try:
            res = requests.post(endpoint, headers=headers, timeout=10)
        except requests.exceptions.RequestException as err:
            return self.errorHandler.handleError('cancel_invoice', err)

        # If error
        if res.status_code != 200:
            return self.errorHandler.handleError(
                'cancel_invoice',
                'Xendit invoice is not found or cancel failed.',
                res.status_code
            )

        if(res.status_code == 200):
            return True

        return False