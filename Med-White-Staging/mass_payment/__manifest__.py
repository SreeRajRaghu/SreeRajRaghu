# -*- encoding: UTF-8 -*-
{
    'name': 'Mass payment to Vendor',
    'version': '1.0',
    'author': 'Sismatix',
    'website': 'http://sismatix.com',
    'category': 'payment',
    'summary': 'Mass Payment',
    'description': '''user can pay at one time or receive payment with diffrent invoice.
''',
    'depends': [
        'account_accountant',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/mass_payment_data.xml',
        # 'wizard/account_general_ledger_wizz.xml',
        # 'wizard/check_report_wizard_view.xml',
        # 'report/accounr_general_ledger.xml',
        'report/mass_payment_report.xml',
        'views/account_payment.xml',
        'views/account_journal_view.xml',
        'views/partner_view.xml',
        'views/report_mass_payment.xml',
        'views/report_payment_transfer.xml',
        'views/report_check_book.xml',
        # 'views/res_company_inherit.xml'
    ],
    'active': True,
    'installable': True,
}
