# -*- coding: utf-8 -*-

{
    'name': 'Medical Front-End',
    'version': '13.0.1.0.1',
    'summary': 'Medical',
    'sequence': 1,
    'author': 'Odoo S.A., Sismatix Co.',
    'website': 'http://sismatix.com',
    'description': """
Medical App
===========
Medical App
    """,
    'category': 'Medical',
    'depends': [
        'medical_app', 'barcodes', 'web_editor', 'hr'
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',

        'views/assets.xml',
        'views/medical_index.xml',

        'views/config_views.xml',
        'views/hr_views.xml',

        'views/account_views.xml',
        'views/payment_views.xml',
        'views/prepaid_views.xml',

        'views/report_resource_summary.xml',
        'wizard/resource_app_views.xml',
        'wizard/appointment_report.xml',
        

        'report/report_session_summary.xml',
        'wizard/session_summary_report_wiz.xml',
        'wizard/journal_items_report.xml',
        'report/report_menu.xml',

        'wizard/ssn_summary_by_config_views.xml',
        'report/report_session_summary_by_config.xml',

        'views/appointment_views.xml',
        # 'views/multi_order_views.xml',

        'views/discount_reason_views.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'application': True,
}
