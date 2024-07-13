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
    'name': 'BIRTUM | Fast Invoicing Sale Order',
    'author': 'BIRTUM ©',
    'category': 'Website',
    'sequence': 50,
    'summary': """ Invoicing sale order from website""",
    'website': 'https://www.birtum.com',
    'version': '16.0',
    'license': 'OPL-1',
    'description': """
        Search and invoice sale orders from website.
    """,
    
    'depends': [
        'b_fast_invoicing'
    ],
    'assets': {
        'web.assets_frontend': [
            'b_fast_invoicing/static/src/scss/b_fast_invoicing.scss',
            'b_fast_invoicing/static/src/js/misc.js',
            'b_fast_invoicing/static/src/js/b_fast_invoicing.js',
            'b_fast_invoicing/static/src/xml/throbber.xml',
        ],
        'point_of_sale.assets': [
            'b_fast_invoicing/static/src/js/models.js',
            'b_fast_invoicing/static/src/xml/inherit_pos_ticket.xml',
        ],
    },
    'data': [
        'views/inherit_orders_views.xml',
        'views/inherit_sale_order_report_view.xml',
    ],
    'qweb': [],
    'demo': [
    ],
    'installable': True,
    'application': False,
}
