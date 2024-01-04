{
    'name': 'Medical PCR Request',
    'version': '13.0.3',
    'author': "Sismatix",
    'category': 'Generic Modules/Medical',
    'summary': 'Medical Lab Solutions',
    'depends': ['medical_lab'],
    'description': " ",
    "website": "http://sismatix.com",
    "data": [
        'sequence/sequence.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/data.xml',

        'views/airline_views.xml',

        'views/assets.xml',
        'views/pcr_test_views.xml',

        'views/pcr_request.xml',
        'views/pcr_template.xml',
        'report/pcr_qr_code.xml',
        'report/report_pcr_certificate.xml',
        # 'report/layout.xml',
        'report/pcr_report_templates.xml',
        'report/pcr_vaccinated.xml',

        'views/company_views.xml',
        'views/product_views.xml',

        'wizard/pcr_test_transfer_views.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    "images": ['images/main_screenshot.png'],
}
