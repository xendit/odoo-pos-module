# -*- coding: utf-8 -*-
from odoo import models, fields

class XenditCredentials(models.TransientModel):
    _inherit = 'res.config.settings'    
    _name = "xendit.credentials"    
    
    public_key = fields.Char(string='Public Key', required=True)    