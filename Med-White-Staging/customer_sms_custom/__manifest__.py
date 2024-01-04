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
        # 'security/ir.model.access.csv',
        'security/security.xml',
        'data/sms_templates.xml',
        'views/sms_config_view.xml',
        'wizard/sms_send_wizard.xml',
        'wizard/customer_sms_wizard.xml',
        'views/menus.xml',
    ],
}
