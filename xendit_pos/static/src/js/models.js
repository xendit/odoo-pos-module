odoo.define('xendit_pos.models', function (require) {
  const { register_payment_method, Payment } = require('point_of_sale.models')
  const PaymentXendit = require('xendit_pos.payment')
  const Registries = require('point_of_sale.Registries')

  register_payment_method('xendit_pos', PaymentXendit)

  const PosXenditPayment = (Payment) => class PosXenditPayment extends Payment {
    constructor (obj, options) {
      super(...arguments)
      this.xenditInvoiceId = this.xenditInvoiceId || null
    }

    // @override
    export_as_JSON () {
      const json = super.export_as_JSON(...arguments)
      json.xendit_invoice_id = this.xenditInvoiceId
      return json
    }

    // @override
    init_from_JSON (json) {
      super.init_from_JSON(...arguments)
      this.xenditInvoiceId = json.xendit_invoice_id
    }

    setXenditInvoiceId (id) {
      this.xenditInvoiceId = id
    }

    getXenditInvoiceId () {
      return this.xenditInvoiceId
    }
  }
  Registries.Model.extend(Payment, PosXenditPayment)
})
