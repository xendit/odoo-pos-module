# -*- coding: utf-8 -*-
from odoo import models, fields

class XenditSettings(models.TransientModel):   
    _inherit = "res.config.settings"
    
    secret_key = fields.Char('Secret Key')

    def set_values(self):
       """xendit setting field values"""
       res = super(XenditSettings, self).set_values()  
       self.env['ir.config_parameter'].set_param('xendit.secret_key', self.secret_key)
       return res

    def get_values(self):
       """xendit limit getting field values"""
       res = super(XenditSettings, self).get_values()
       secret_key_value = self.env['ir.config_parameter'].sudo().get_param('xendit.secret_key')
       res.update(
           secret_key=str(secret_key_value)
       )
       return res