# -*- coding: utf-8 -*-
{
    'name': "Xendit POS",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Xendit",
    'website': "https://xendit.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sales',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale'],

    # always loaded
    'data': [
        'views/pos_payment_method_views.xml',
        'views/point_of_sale_assets.xml'
    ],
    'qweb': [
        'views/xendit_receipt.xml', 
        'static/src/xml/pos.xml', 
        'static/src/xml/xendit_qrcode_popup.xml'
    ],
    'images': ['static/description/icon.png'],
    'application': True,
    'installable': True
}
