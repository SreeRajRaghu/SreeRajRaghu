# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Med-White Customization',
    'author': 'Sismatix Co.',
    'website': 'http://sismatix.com/',
    'description': '''
    ''',
    'category': 'Custom',
    'version': '13.0.5',
    'depends': [
        'purchase_stock', 'smsbox', 'boutiqaat_hr_base', 'hr_payroll_account',
        'mass_payment', 'account', 'purchase', 'medical_js', 'dashboard_data',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/gold_dashboard_line.xml',
        'views/purchase_views.xml',
        'views/budget_view.xml',
        'views/emp_views.xml',
        'views/mass_payment_change.xml',
        'views/medwhite_gold.xml',
        'wizards/department_report_view.xml',
        'wizards/cash_report_view.xml'
    ],
}
