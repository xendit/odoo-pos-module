# -*- coding: utf-8 -*-
from ast import In, Or
import base64
from operator import or_
import random
import string
import qrcode
import qrcode.image.svg
import io

class DataUtils():

    def isEmptyString(self, str):
        return not (str and str.strip())

    def encodeSecretKey(self, secret_key):
        secret_key = secret_key + ':'
        secret_key_bytes = secret_key.encode('ascii')
        base64_bytes = base64.b64encode(secret_key_bytes)
        return base64_bytes.decode('ascii')

    def generateInvoiceItems(self, data):
        items = []
        for orderline in data['orderlines']:
            itemPrice = orderline['price']
            itemQuantity = orderline['quantity']

            # Currently we don't support the item has price = 0
            if itemQuantity > 0:
                item = {
                    'name': orderline['product_name'],
                    'price': itemPrice,
                    'quantity': itemQuantity
                }
                items.append(item)

        return items


    def generateInvoiceAddress(self, data):
        addresses = []
        if data == None:
            return addresses

        address = {}
        if not self.isEmptyString(data['city']):
            address['city'] = data['city']

        if not self.isEmptyString(data['country_id'][1]):
            address['country'] = data['country_id'][1]

        if not self.isEmptyString(data['zip']):
            address['postal_code'] = data['zip']

        if not self.isEmptyString(data['state_id'][1]):
            address['state'] = data['state_id'][1]

        if not self.isEmptyString(data['street']):
            address['street_line1'] = data['street']

        addresses.append(address)
        return addresses


    def generateInvoiceCustomer(self, data):

        customerObject = {}
        if data == None:
            return customerObject

        if not self.isEmptyString(data['name']):
            customerObject['given_names'] = data['name']

        if not self.isEmptyString(data['email']):
            customerObject['email'] = data['email']

        if not self.isEmptyString(data['phone']):
            customerObject['mobile_number'] = data['phone']

        customerAddressObject = self.generateInvoiceAddress(data)
        if customerAddressObject != None:
            customerObject['addresses'] = customerAddressObject

        return customerObject

    def generateHeader(self, secret_key, plugin_name, plugin_version):

        encodedSecretKey = ''
        if not self.isEmptyString(secret_key):
            encodedSecretKey = self.encodeSecretKey(secret_key)

        return {
            'content-type': 'application/json',
            'x-plugin-name': plugin_name,
            'x-plugin-version': plugin_version,
            'Authorization': 'Basic ' + encodedSecretKey
        }

    def initQrCode():
        return qrcode.QRCode(  
            version = 1,  
            error_correction = qrcode.constants.ERROR_CORRECT_L,  
            box_size = 10,  
            border = 4,  
        )  

    def generateQrCode(self, xendit_invoice_url):
        qrcode_image = qrcode.make(xendit_invoice_url)
        stream = io.BytesIO()
        qrcode_image.save(stream)
        return base64.b64encode(stream.getvalue()).decode("utf-8")

