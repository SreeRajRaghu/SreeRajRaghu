# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Med-White HR PAYSLIP GROUP',
    'version': '1.0',
    'author': 'Sismatix Co.',
    'website': 'http://sismatix.com/',
    'description': '''
    ''',
    'category': 'Custom',
    'version': '1.0',
    'depends': ['purchase_stock', 'hr_payroll', 'hr_payroll_account'],
    'data': [
        'security/ir.model.access.csv',
        'views/wizard_group_payslip.xml',
        'views/contract_view.xml',

    ],
}
