{
    'name': 'Menu Access Right',
    'version': '13.0.1.0.0',
    'summary': 'Manage Loan Requests',
    'description': """
        Helps you to manage menu access right.
        """,
    'category': 'Generic Modules/Human Resources',
    'depends': ['account', 'base'],
    'data': [
        'security/security.xml',
        'views/res_users_inherit.xml',
        'views/account_payment_inherit.xml',
        'views/invoice_inherit.xml',
        'menus/menu.xml'
    ],
    'demo': [],
    'images': [],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
