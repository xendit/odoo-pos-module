odoo.define('xendit_pos.XenditQRCodePopup', function (require) {
  'use strict'
  const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup')
  const Registries = require('point_of_sale.Registries')

  class XenditQRCodePopup extends AbstractAwaitablePopup {
    get currentOrder () {
      return this.env.pos.get_order()
    }
  }

  // Create products popup
  XenditQRCodePopup.template = 'XenditQRCodePopup'
  XenditQRCodePopup.defaultProps = {
    confirmText: 'Ok',
    cancelText: 'Cancel',
    title: 'Xendit QRcode',
    body: '',
    xenditPaymentStatus: 'Processing...',
    invoiceUrl: '',
    qrCodeImage: ''
  }
  Registries.Component.add(XenditQRCodePopup)
  return XenditQRCodePopup
})
