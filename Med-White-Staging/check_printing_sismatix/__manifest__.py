# -*- coding: utf-8 -*-
{
    'name': 'Sismatix Checks Layout',
    'version': '1.0',
    'category': 'Accounting/Accounting',
    'summary': 'Print Checks',
    'description': """
    """,
    'website': 'https://www.odoo.com/page/accounting',
    'depends': ['account_check_printing'],
    'data': [
        'data/check_printing.xml',
        'report/print_check.xml',
        'report/print_check_top.xml',
        'report/print_check_middle.xml',
        'report/print_check_bottom.xml',
    ],
    'installable': True,
    'auto_install': True,
}
