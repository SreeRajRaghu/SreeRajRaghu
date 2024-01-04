# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Med-White Customization',
    'version': '13.0.1',
    'author': 'Sismatix Co.',
    'website': 'http://sismatix.com/',
    'description': '''
    ''',
    'category': 'Custom',
    'version': '1.0',
    'depends': [
        'purchase_stock', 'smsbox', 'boutiqaat_hr_payslip', 'hr_payroll_account', 'hr_employee_eos',
        'medical_report',
    ],
    'data': [
        "data/data.xml",
        "report/eos_format2.xml",
        "views/payslip_views.xml",
    ],
}
