# -*- encoding: utf-8 -*-
#
# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2023 Birtum - http://www.birtum.com/
# All Rights Reserved.
#
# Developer(s): Eddy Luis Pérez Vila
#               (epv@birtum.com)
########################################################################
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
########################################################################
{
    'name': 'BIRTUM | Custom Views',
    'author': 'BIRTUM ©',
    'category': 'Website',
    'sequence': 50,
    'summary': """ Custom Views""",
    'website': 'https://www.birtum.com',
    'license': 'OPL-1',
    'version': '16.1.1.3',
    'depends': [
        'account',
        'sale',
        'sale_margin',
    ],
    'data': [
        'security/security.xml',
        'views/account_move_view.xml',
        'views/inherit_sale_order_views.xml',
    ],
    'qweb': [
    ],
    'demo': [
    ],
    'installable': True,
    'application': False,
}
