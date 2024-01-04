# -*- coding: utf-8 -*-

{
    'name': 'Medical Front-End - Hr Holidays',
    'version': '13.0.1.0.0',
    'summary': 'Medical',
    'sequence': 1,
    'author': 'Odoo S.A., Sismatix Co.',
    'website': 'http://sismatix.com',
    'description': """
Medical Js - Hr Holidays
==============================
    """,
    'category': 'Medical',
    'depends': [
        'medical_js', 'hr_holidays',
    ],
    'data': [
        'views/config_views.xml',
    ],
    "auto_install": True,
}
