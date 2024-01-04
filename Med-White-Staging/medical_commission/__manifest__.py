# -*- coding: utf-8 -*-
{
    'name': 'Medical Resource Commission',
    'version': '1.0',
    'author': 'Sismatix Co.',
    'website': 'http://sismatix.com/',
    'description': '''
- Product: Inside / Outside Test
- Resource - Set Commission Rate
- On Invoice Post - Auto Compute Bill of Commission
    ''',
    'category': 'Medical',
    'version': '1.0',
    'depends': ['medical_lab'],
    'data': [
        'views/medical_resource.xml',
        'views/product_view.xml',
    ],
}
