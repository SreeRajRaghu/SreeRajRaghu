# -*- coding: utf-8 -*-
{
    'name': 'US Checks Layout Extended',
    'version': '1.0',
    'category': 'Accounting/Accounting',
    'description': """
    """,
    'website': 'https://www.odoo.com/page/accounting',
    'depends': ['check_printing_sismatix'],
    'data': [
        'data/extended_view_data.xml',
        'report/payment_report.xml',
        'report/print_check.xml',
        'report/print_check_top.xml',
        'report/receipt_voucher_view.xml',
        'report/payment_voucher_view.xml',
        'views/payment_view.xml',
    ],
    'installable': True,
}
