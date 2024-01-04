# -*- coding: utf-8 -*-

{
    'name': 'HR Payslip Employee Inputs',
    'version': '13.0.1',
    'sequence': 1,
    'category': 'Sismatix-HR',
    'author': 'Sismatix',
    'description': """
    """,
    'website': 'https://sismatix.com',
    'depends': ['hr_payroll'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',

        'data/input_data.xml',

        'views/emp_inputs_views.xml',
        'views/employee_views.xml',
        'views/bulk_input_views.xml',
        'views/bulk_input_views.xml',
    ],
}
