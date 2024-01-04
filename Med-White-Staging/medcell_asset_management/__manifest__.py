# -*- coding: utf-8 -*-
# /#############################################################################
#
#    Akira Software Solutions Pvt. Ltd.
#    Copyright (C) 2004-TODAY Akira Software(<http://akiraplc.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# /#############################################################################
{
    'name': 'Medcell Asset Management',
    'version': '1.0',
    'category': 'Inventory',
    "sequence": 3,
    'summary': 'Medcell Asset Management',
    'complexity': "User Friendly",
    'description': """
            This module provide Asset management system

    """,
    'author': 'Ajith Sures',
    'depends': ['base', 'mail', 'hr', 'product'],
    'data': [
        'data/product_seq_code.xml',
        'security/medcell_asset_management.xml',
        'security/ir.model.access.csv',
        'views/medcell_product_category_view.xml',
        'views/medcell_asset_management_room_view.xml',
        'views/medcell_asset_management_building_view.xml',
        'views/medcell_floor_block_view.xml',
        'wizard/move_asset.xml',
        'wizard/asset_move_issue.xml',
        'wizard/asset_move_return.xml',
        'wizard/generate_bulk_asset.xml',
        'views/asset_movement.xml',
        'views/medcell_asset_brand.xml',
        'views/asset_menagement_menus.xml',
        'reports/product_qr_code.xml',
        'reports/cabin_report.xml',
        'reports/asset_issue_receipt.xml',
        'reports/asset_return_receipt.xml',
        'reports/reports_menu.xml',
    ],

    'installable': True,
    'auto_install': False,
    'application': True,
}
