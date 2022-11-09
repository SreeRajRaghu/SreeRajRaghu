{
    'name': 'Dropbox Configurations',
    'version': '1.0',
    'category': '',
    "sequence": 15,
    'category': 'SmartSchool',
    'description': """
     *  This module creates the SmartSchool Dropbox settings view.
    """,
    'depends': ['base', 'web', 'account', 'smartschool_base'],
    'init_xml': [],
    'data': [

        'security/ir.model.access.csv',
        'views/dropbox_settings_view.xml',
        'menus/menu.xml'

    ],
    'demo_xml': [],
    'test': [
    ],
    'qweb': [],
    'installable': True,
    'auto_install': False,
}