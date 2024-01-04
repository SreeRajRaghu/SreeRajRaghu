{
    "name": "Base Notification",
    "version": "1.1",
    'summary': 'Design and Send Notification',
    'description': "",
    'category': 'Marketing',
    "author": "Sismatix",
    "website": "http://sismatix.com",
    "depends": [
        "mail"
    ],
    "data": [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/notif_views.xml',
        'views/sms_template_view.xml'
    ],
    'sequence': 2,
    'application': True,
}
