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
    'name': "BIRTUM | Portal Provider",
    'summary': """Easy For Providers""",
    'description': """
    Updating the SKU of the products from the portal.
    Import and export the list of products for mass update.
    """,

    'sequence': 50,
    'author': "BIRTUM ©",
    'website': 'https://www.birtum.tech',
    'category': 'Extra Tools',
    'version': '16.1.0.1',
    'last_update': '25-09-2023',
    'depends': [
        'base',
        'portal',
        'purchase',
        'web',
        'stock'
    ],
    'assets': {
        'web.assets_frontend': [
            '/b_portal_base/static/src/js/my_products.js',
        ],
    },

    'data': [
        # Security
        'security/ir.model.access.csv',
        #'views/inherit_portal_provider.xml',
        'views/my_products.xml',
        'views/inherit_product_supplierinfo.xml',
       # 'views/res_config_settings_view.xml'
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'license': 'AGPL-3'
}
