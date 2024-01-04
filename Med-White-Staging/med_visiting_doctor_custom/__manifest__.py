# -*- coding: utf-8 -*-

{
    'name': 'Visiting Doctors Report',
    'version': '1.1',
    'category': '',
    'description': '''
    ''',
    'website': '',
    'depends': [
        'account', 'medical_app', 'base', 'medical_commission'
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/commission_report_wizard_view.xml',
        'views/vendor_bill_inherit.xml',
        'views/resource_inherit.xml'
    ],
}
