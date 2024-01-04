{
    'name': 'Schedular for sessions',
    'version': '13.0.1.0.0',
    'summary': 'Schedular for daily session closing',
    'description': """
        Schedular for closing daily opened session to closing automatically.
        """,
    'category': 'Generic Modules',
    'depends': ['medical_app', 'base'],
    'data': [
        'datas/data.xml',
        'views/session_config_inherit.xml',
    ],
    'demo': [],
    'images': [],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
