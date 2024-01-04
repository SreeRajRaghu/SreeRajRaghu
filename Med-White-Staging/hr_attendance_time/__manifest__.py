# -*- coding: utf-8 -*-

{
    'name': 'HR Attendance More Fields',
    'version': '13.0.1',
    'author': 'Sismatix',
    'category': 'Human Resources',
    'description': """
    """,
    'website': 'https://sismatix.com',
    'depends': [
        'hr_attendance',
        'boutiqaat_hr_base',
        'web_tree_dynamic_colored_field',
        'hr_holidays',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/attendance_views.xml',
        'views/views.xml',
        'wizard/attendance_wiz_views.xml',
        'wizard/imp_attendance_views.xml',
        'wizard/imp_contract_views.xml',
        'wizard/att_calendar_views.xml',
    ],
}
