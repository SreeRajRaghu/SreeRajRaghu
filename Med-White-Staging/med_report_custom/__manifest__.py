# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Lab Report Custom',
    'version': '13.0.1.0.1',
    'category': 'Medical report',
    'summary': 'Medical Reports For Odoo 13',
    'sequence': '10',
    'author': 'Odoo Mates, Odoo SA',
    'license': 'LGPL-3',
    'company': 'Odoo Mates',
    'maintainer': 'Odoo Mates',
    'support': 'odoomates@gmail.com',
    'website': '',
    'depends': ['account', 'medical_lab'],
    'live_test_url': '',
    'demo': [],
    'data': [
        'views/medical_department_inherit.xml',
        'reports/report_patient_labtest_inherit.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'qweb': [],
}
