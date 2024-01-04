# -*- coding: utf-8 -*-
{
    'name': "Medical Product Custom",
    'summary': "",
    'author': "",
    'website': "",
    'category': '',
    'version': '13.2.0',
    'sequence': 3,
    'depends': ['base', 'product', 'account', 'sale', 'med_white_base'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_inherit_view.xml',
        'views/account_move_line_inherit.xml',
    ],
}
