# -*- coding: utf-8 -*-
from odoo import models, fields

class SchoolClass(models.Model):    
    _name = "school.class"    
    
    name = fields.Char(string='Name', required=True)