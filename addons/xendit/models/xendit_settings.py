# -*- coding: utf-8 -*-
from odoo import models, fields

class XenditSettings(models.TransientModel):   
    _inherit = "res.config.settings"
    
    public_key = fields.Char('Public Key')
    secret_key = fields.Char('Secret Key')
    test_mode = fields.Boolean('Test Mode')

    def set_values(self):
       """xendit setting field values"""
       res = super(XenditSettings, self).set_values()  
       self.env['ir.config_parameter'].set_param('xendit.public_key', self.public_key)
       self.env['ir.config_parameter'].set_param('xendit.secret_key', self.secret_key)
       self.env['ir.config_parameter'].set_param('xendit.test_mode', self.test_mode)
       return res

    def get_values(self):
       """xendit limit getting field values"""
       res = super(XenditSettings, self).get_values()
       public_key_value = self.env['ir.config_parameter'].sudo().get_param('xendit.public_key')
       secret_key_value = self.env['ir.config_parameter'].sudo().get_param('xendit.secret_key')
       test_mode_value = self.env['ir.config_parameter'].sudo().get_param('xendit.test_mode')
       res.update(
           public_key=str(public_key_value),
           secret_key=str(secret_key_value),
           test_mode=bool(test_mode_value),
       )
       return res