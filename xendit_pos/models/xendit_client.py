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
from . import data_utils

class XenditClient():

    tpi_server_url = "https://tpi.xendit.co"
    odoo_company_id = ""

    dataUtils = data_utils.DataUtils()

    def _set_odoo_company_id(self, company_id):
        self.odoo_company_id = company_id
        return self

    def _get_xendit_payment_method(self):
        return request.env['pos.payment.method'].sudo().search(
                [
                    ('use_payment_terminal', '=', 'xendit_pos'),
                    ('company_id', '=', self.odoo_company_id)
                ],
                limit=1
            )

    def _get_xendit_secret_key(self):
        xendit_payment_method = self._get_xendit_payment_method(self)
        return xendit_payment_method.xendit_pos_secret_key

    def _generate_header(self):
        return self.dataUtils.generateHeader(
            self._get_xendit_secret_key(self)
        )

    def _generate_payload(self, data):

        customerObject = self.dataUtils.generateInvoiceCustomer(data['client'])
        payload = {
            "external_id": data["name"].split(" ")[1],
            "amount": data["total_rounded"],
            "currency": data["currency"]["name"],
            "description": data["name"],
            "items": self.dataUtils.generateInvoiceItems(data),
            "customer": customerObject,
            "client_type": "INTEGRATION",
        }

        if len(customerObject) > 0 and not self.dataUtils.isEmptyString(customerObject["email"]):
            payload['payer_email'] = customerObject["email"]

        return payload

    def _create_invoice(self, data):

        endpoint = self.tpi_server_url + '/payment/xendit/invoice'
        headers = self._generate_header(self)
        payload = self._generate_payload(self, data)

        try:
            res = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        except requests.exceptions.RequestException as err:
            print ("OOps: ",err)

        response = json.loads(res.text)

        # If error
        if res.status_code != 200:
            return {
                'error': {
                    'status_code': res.status_code,
                    'message': response["message"]
                }
            }

        return response

    def _get_invoice(self, invoice_id):

        endpoint = self.tpi_server_url + '/payment/xendit/invoice/' + invoice_id
        headers = self._generate_header(self)

        try:
            res = requests.get(endpoint, headers=headers, timeout=10)
        except requests.exceptions.RequestException as err:
            print ("OOps: ",err)

        response = json.loads(res.text)

        # If error
        if res.status_code != 200:
            return {
                'error': {
                    'status_code': res.status_code,
                    'message': response["message"]
                }
            }

        return response
