# -*- coding: utf-8 -*-
{
    'name': "Med-White Odoo Integration With MSSQL",
    'summary': "Med-White Odoo Integration With MSSQL",
    'author': "Sismatix",
    'website': "http://sistimax.com",
    'category': 'Sismatix',
    'version': '1.0',
    'sequence': 3,
    "external_dependencies": {"python": ['pymssql'], "bin": []},
    'depends': ['medical_app', 'medical_lab'],
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/mssql_config_view.xml',
        'views/medical_lab_view.xml',
    ],
}
