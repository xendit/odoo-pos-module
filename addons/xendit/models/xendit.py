# -*- coding: utf-8 -*-
from odoo import models, fields

class Xendit(models.Model):   
    _name = "xendit.xendit"
    
    name = fields.Char('Name')