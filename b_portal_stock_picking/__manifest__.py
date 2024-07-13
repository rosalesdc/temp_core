# -*- encoding: utf-8 -*-
#
# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2023 Birtum - http://www.birtum.com
# All Rights Reserved.
#
# Developer(s): Carlos Maykel López González
#               (clg@birtum.com)
#
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
    'name': 'BIRTUM | Portal Stock Picking Info',
    'author': 'BIRTUM ©',
    'category': 'Extra Tools',
    'sequence': 50,
    'summary': " Add Efective Date transfer and delivery slip report in portal provider.",
    'website': 'https://www.birtum.com',
    'version': '16.1.0.1',
    'description': """Add Efective Date transfer and delivery slip report in portal provider.""",
    'depends': ['base', 'b_portal_base', 'website', 'purchase', 'stock', 'purchase_stock', 'portal', 'web'],
    'data': [
        'views/templates.xml',
        'views/inherit_portal_provider.xml',
        'views/inherit_stock_picking_view.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            '/b_portal_stock_picking/static/src/js/download_stock_picking.js',
            '/b_portal_stock_picking/static/src/js/invoicing.js',
            '/b_portal_stock_picking/static/src/js/add_pdf.js',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
