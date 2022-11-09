# -*- coding: utf-8 -*-
#/#############################################################################
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
#    By ABHINAV
#/#############################################################################
# Commit 3
{
    'name': 'Daily Examination Module',
    'version': '1.0',
    'category': 'Customize Module',
    "sequence": 3,
    'summary': 'Customize Module',
    'complexity': "User Friendly",
    'description': """

    """,
    'author': 'Akira Software Solutions Pvt. Ltd.',
    'website': 'http://www.akiraplc.com',
    'images': [],
    'depends': ['base', 'smartschool_exam', 'smartschool_base'],
    'data': [
        'security/ir.model.access.csv',
        'views/daily_exam.xml',
        'views/ss_student_inherit.xml',
        'menus/menus.xml'
    ],
    'css': [],
    'qweb': [],
    'js': [],
    'images': [],
    'installable': True,
    'auto_install': True,
    'application': True,
}