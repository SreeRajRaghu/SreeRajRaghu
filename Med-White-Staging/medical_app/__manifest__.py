# -*- coding: utf-8 -*-

{
    'name': 'Medical App',
    'version': '13.0.9',
    'summary': 'Medical App',
    'sequence': 1,
    'author': 'Sismatix Co.',
    'website': 'http://sismatix.com',
    'description': """
Medical App
=============
Core Medical App
    """,
    'category': 'Medical',
    'depends': [
        'hr',
        'contacts',
        'stock_account',
        'web_widget_colorpicker',
        'web_gantt',
        'account_invoice_fixed_discount',
        'product',
        'account',
    ],
    'data': [
        'security/medical_app_security.xml',
        'security/ir.model.access.csv',
        'data/medical_config.xml',
        'data/attachment_data.xml',
        'data/sequence_data.xml',
        'data/medical_state_data.xml',
        'data/last_action_data.xml',
        'data/complain.type.csv',
        'wizard/update_resource_wizard.xml',
        'views/menus.xml',
        'views/medical_views.xml',
        'views/company_views.xml',
        'views/partner_views.xml',
        'views/medical_config_views.xml',
        'views/medical_resource_views.xml',
        'views/session_views.xml',
        'views/medical_order_views.xml',
        'views/medical_state_views.xml',
        'views/medical_attachment_type_views.xml',
        'views/waiting_list_views.xml',
        'views/medical_reminder_views.xml',
        'views/medical_patient_attachment_views.xml',
        'views/medical_customer_package_views.xml',
        'views/product_views.xml',
        'views/pricelist_views.xml',
        'views/stock_views.xml',
        'views/insurance_views.xml',
        'views/account_views.xml',
        'views/hr_views.xml',
        'views/medical_clinic_views.xml',
        'views/last_action_views.xml',
        'views/complain_views.xml',
    ],
    'application': True,
}
