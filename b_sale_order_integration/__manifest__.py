# -*- encoding: utf-8 -*-
#
# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2023 Birtum - https://www.birtum.com
# All Rights Reserved.
#
# Developer(s): David Rosales
#               drc@birtum.com
#######################################################################
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#######################################################################

{
    'name': 'BIRTUM  | Sale Order Integration',
    'author': 'BIRTUM ©',
    'category': 'Sales',
    'sequence': 50,
    'summary': """Receive and process incoming data for Sales Orders.""",
    'website': 'https://www.birtum.com',
    'version': '16.1.1.0',
    'last_update': '08-07-2024',
    'description': """
BIRTUM | Sale Order Integration

""",
    'depends': [
        'base',
        'sale',
        'stock',
        'purchase',
        'account',
        'w_sync_generic',
    ],
    'data': [
        'security/ir.model.access.csv',
        #'data/ir_cron.xml',
        'views/so_integrated_data_views.xml',
        'views/inherit_res_partner_views.xml',
        'views/inherit_res_company_views.xml',
        'views/inherit_sale_order_views.xml',
        'views/inherit_account_payment_views.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
