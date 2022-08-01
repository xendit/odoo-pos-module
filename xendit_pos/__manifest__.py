# -*- coding: utf-8 -*-
{
    'name': "Xendit POS",
    'license': 'LGPL-3',
    'summary': """
        Xendit is a leading payment gateway for Indonesia, the Philippines and Southeast Asia.
        """,

    'description': """
        Xendit is a leading payment gateway for Indonesia, the Philippines and Southeast Asia.
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
    'images': [
        'static/description/cover.png'
    ],
    'application': True,
    'installable': True
}
