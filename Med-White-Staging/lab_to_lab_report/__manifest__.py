# -*- coding: utf-8 -*-

{
    'name': 'Lab-Lab Reports',
    'version': '13.0.5',
    'summary': '',
    'sequence': 2,
    'author': '',
    'website': '',
    'description': """
Lab to Lab Reports
===================
    """,
    'category': 'Medical Lab',
    'depends': [
        'medical_app', 'account', 'medical_lab'
    ],
    'data': [
        'views/lab_test_inherit.xml',
        'wizard/lab_report_wiz.xml'
    ],
}
