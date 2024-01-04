# -*- coding: utf-8 -*-

{
    'name': 'HR Leave Encashment',
    'version': '1.1',
    'category': '',
    'description': '''HR Leave Encashment''',
    'website': '',
    'depends': ['hr', 'hr_holidays', 'hr_attendance_time', 'account', 'branch'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_views.xml',
        'views/res_config_inherit.xml',
        'wizard/make_payment_wiz.xml',
        'views/hr_encash_history.xml',
        'wizard/hr_encash_wizard.xml',
        'views/menus.xml'
    ],
}
