# -*- coding: utf-8 -*-

{
    'name': 'Leave Approver',
    'version': '1.1',
    'category': 'Sismatix-HR',
    'description': '''
    ''',
    'website': 'https://sismatix.com',
    'depends': [
        'hr_holidays',
        'hr_attendance_time', 'hr_leave_payment'
    ],
    'data': [
        'security/hr_leave_custom_security.xml',
        'security/ir.model.access.csv',
        'data/hr_leave_data.xml',
        'views/hr_views.xml',
        'wizard/resume_work_wizard_view.xml',
        'wizard/import_hr_leave_view.xml',
    ],
}
