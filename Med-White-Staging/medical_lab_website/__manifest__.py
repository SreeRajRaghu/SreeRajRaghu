# -*- coding: utf-8 -*-

{
    'name': 'Medical Test Lab Website',
    'category': 'Website/Website',
    'sequence': 170,
    "author": "Sismatix",
    'summary': 'Publish Appointment req',
    "website": "http://sismatix.com",
    'description': "",
    'depends': ['medical_lab', 'web_editor','website'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/appoinment_create.xml',
        'views/medical_lab_portal_templates.xml',
        'views/footer.xml',
        'views/medical_views.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
    'application': True,
}
