# -*- coding: utf-8 -*-
{
    'name': "SMSBOX",
    'summary': "Easy SMS",
    'author': "Sismatix",
    'website': "http://sistimax.com",
    'category': 'Sismatix',
    'version': '13.2.0',
    'sequence': 3,
    'depends': ['base_notification', 'medical_app'],
    'data': [
        'security/ir.model.access.csv',
        'data/sms_templates.xml',
        'views/sms_config_view.xml',
        'views/sms_history.xml',
        'wizard/sms_send_wizard.xml'
    ],
}
