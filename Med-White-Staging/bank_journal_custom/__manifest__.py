{
    "name": "Discount for bank journal",
    "version": "1.1",
    'summary': 'Banking Journal for payment',
    'description': "",
    'category': '',
    "author": "",
    "website": "",
    "depends": ["account", "branch"
                ],
    "data": [
        'wizard/register_payment_wiz.xml',
        'views/account_journal_inherit.xml',
        'views/account_move_inherit.xml'
    ],
    'sequence': 2,
    'application': True,
}
