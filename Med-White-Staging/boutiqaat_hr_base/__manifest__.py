# -*- coding: utf-8 -*-

{
    'name': 'Boutiqaat HR Base',
    'version': '1.0',
    'category': 'Human Resources',
    'description': """
    """,
    'website': 'https://sismatix.com',
    'depends': [
        'hr_default',
        # 'hr_leave_payment',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/boutiqaat_hr_base_data.xml',
        'views/views.xml',
        'views/hr_emp_discount_views.xml',
        'views/hr_views.xml',
        'views/hr_holidays_views.xml',
        'views/hr_mail_notification_view.xml',
        'views/res_views.xml',
        'wizard/import_employee_wizard_view.xml',
    ],
}
