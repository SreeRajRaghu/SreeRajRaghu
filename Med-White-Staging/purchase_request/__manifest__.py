{
    'name': "Purchase Request",

    'summary': "",
    'author': '',
    'website': "",
    'category': 'Purchase Request',
    'version': '13.0.1.0',
    'license': 'AGPL-3',
    'depends': [
        'base', 'web', 'branch', 'purchase'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/request_data.xml',
        'wizards/issue_available_qty_wiz.xml',
        'wizards/change_qty_wiz.xml',
        'views/purchase_request.xml',
        'views/ir_config_inherit.xml',
        'views/purchase_order_inherit.xml',
        'views/purchase_requisition_inherit.xml',
        'menus/menu.xml'
    ],

    'installable': True,
}
