# -*- coding: utf-8 -*-

{
    'name': 'Medical App - Reports',
    'version': '13.0.5',
    'summary': 'Medical App',
    'sequence': 2,
    'author': 'Sismatix Co.',
    'website': 'http://sismatix.com',
    'description': """
Medical Reports
===================
Core Medical Reports
    """,
    'category': 'Medical',
    'depends': [
        'medical_app',
    ],
    'data': [
        'data/paperformat_template.xml',
        'report/payment_receipt.xml',
        'report/report_patient_invoice.xml',
        'report/report_patient_ins_invoice.xml',
        'report/report_ins_comp_invoice.xml',
        'report/report_layout.xml',
        'views/report_medical_appointments.xml',
        'views/reports.xml',
        'views/report_patient_file.xml',
        'views/report_patient_sticker.xml',

        'views/company_views.xml',
    ],
}
