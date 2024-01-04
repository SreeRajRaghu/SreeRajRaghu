# -*- coding: utf-8 -*-

{
    'name': 'Boutiqaat HR Contract',
    'version': '1.0',
    'sequence': 1,
    'category': 'Sismatix-HR',
    'description': """
    """,
    'website': 'https://sismatix.com',
    'depends': ['hr_contract', 'boutiqaat_hr_base'],
    'data': [
        'wizard/upd_contract_views.xml',
        'views/contract_views.xml',
        'views/working_schedule_views.xml',
        'wizard/increment_contract_views.xml',
    ],
}
