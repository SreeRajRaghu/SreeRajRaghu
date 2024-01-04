{
    'name': 'Medical Lab',
    'version': '1.0',
    'author': "Sismatix",
    'category': 'Generic Modules/Medical',
    'summary': 'Medical Lab Solutions',
    'depends': ['medical_js', 'hr'],
    'description': " ",
    "website": "http://sismatix.com",
    "data": [
        'security/security.xml',
        'sequence/sequence.xml',
        'data/paperformat_template.xml',
        'data/lab_test_units.xml',
        'data/lab_test_types.xml',
        'data/report_layout.xml',
        'views/report_patient_labtest.xml',
        # 'views/lab_req_form.xml',

        'wizard/wiz_multi_case_views.xml',

        'views/medical_lab_view.xml',
        'views/lab.xml',
        'views/email_sms_button.xml',

        'security/menu_rights.xml',
        'security/ir.model.access.csv',
        # 'security/ir.rule.xml',
        'views/report_lab_sample.xml',
        'views/report_lab_barcode.xml',

        'wizard/wiz_emp_views.xml',
    ],
    "images": ['images/main_screenshot.png'],
    "active": False
}
