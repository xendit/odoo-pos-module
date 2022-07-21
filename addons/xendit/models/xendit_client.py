# -*- coding: utf-8 -*-
from ast import In
import secrets
import this
from wsgiref import headers
import json
import requests
import base64

from odoo import models, fields

class XenditClient(models.TransientModel):   
    _inherit = "res.config.settings"
    
    xendit_test_mode = fields.Boolean(help='Run transactions in the test environment.')
    xendit_secret_key = 'xnd_development_mLcDGtYo1MIqMfbEX2EKO0ktkWlXqEaUnD2hCxgTDEnMGszmWu5dZWDpEVMKeK'
    tpi_server_domain = "https://tpi.xendit.co"

    def _generate_address(data):
        addresses = []

        if data["client"] == None:
            return addresses

        if data["client"]["city"] : city = data["client"]["city"]
        if data["client"]["country_id"] : country = data["client"]["country_id"][1]
        if data["client"]["zip"] : postal_code = data["client"]["zip"]
        if data["client"]["state_id"] != "" : state = data["client"]["state_id"][1]
        if data["client"]["street"] != "" : street = data["client"]["street"]

        address = {
            "city": city,
            "country": country,
            "postal_code": postal_code,
            "state": state,
            "street_line1": street
        }
        addresses.append(address)
        return addresses

    def _generate_customer(self, data):

        if data["client"] == None:
            return {}

        if data["client"]["name"] : name = data["client"]["name"]
        if data["client"]["email"] : email = data["client"]["email"]
        if data["client"]["phone"] : phone = data["client"]["phone"]

        return {
            "given_names": name,
            "email": email,
            "mobile_number": phone,
            "address": self._generate_address(data)
        }

    def _generate_notification(self):
        notificationReferences = {
            "whatsapp",
            "sms",
            "email",
            "viber"
        }
        return {
            "invoice_created": notificationReferences,
            "invoice_reminder": notificationReferences,
            "invoice_paid": notificationReferences,
            "invoice_expired":  notificationReferences
        }

    def _generate_items(data):
        items = []

        for orderline in data["orderlines"]:
            item = {
                "name": orderline["product_name"],
                "price": orderline["price"],
                "quantity": orderline["quantity"]
            }
            items.append(item)
        return items

    def _encodeAPIKey(self):
        secret_key = self.xendit_secret_key + ":"
        secret_key_bytes = secret_key.encode('ascii')
        base64_bytes = base64.b64encode(secret_key_bytes)
        return base64_bytes.decode('ascii')

    def _genenrate_header(self):
        return {
            'content-type': 'application/json',
            'x-plugin-name': 'ODOO_POS',
            'x-plugin-version': '1.0',
            'Authorization': 'Basic ' + self._encodeAPIKey(self)
        }

    def _generate_payload(self, data):
        customer = self._generate_customer(self, data)
        return {
            "external_id": data["name"].split(" ")[1],
            "amount": data["total_rounded"],
            "currency": 'IDR',
            "payer_email": customer["email"] if len(customer) > 0 else "test@example.com",
            "description": data["name"],
            "items": self._generate_items(data),
            "customer": customer,
            "client_type": "INTEGRATION",
        }

    def _create_invoice(self, data):
        endpoint = self.tpi_server_domain + '/payment/xendit/invoice'
        headers = self._genenrate_header(self)
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
        endpoint = self.tpi_server_domain + '/payment/xendit/invoice/' + invoice_id
        headers = self._genenrate_header(self)

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