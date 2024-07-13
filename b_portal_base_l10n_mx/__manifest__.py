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
    'name': 'BRITUM | Portal Provider with l10n_mx',
    'version': '16.1.0.1',
    'last_update': '20-10-2023',
    'summary': """
        Add XML to the purchase order from the portal provider. 
        Create an invoice from the XML or attach XML the file to an invoice
    """,
    'description': """
        Add XML to the purchase order from the portal provider. 
        Create an invoice from the XML or attach the file to an invoice.
        Add a res_config field :
        * portal_xml_state -> default state for account move created in the process
        
        Templates:
        Add templates to add all modals for the process.
        Edit  purchase.portal_my_purchase_orders do add the button and all templates created.
    """,
    'category': 'Extra Tools',
    'author': 'BRITUM ©',
    'website': 'https://www.birtum.com',
    'license': 'AGPL-3',
    'depends': [
        'b_portal_base',
        'base',
        'account',
        'account_accountant',
        'l10n_mx',
        'l10n_mx_edi',
        'sale',
        'stock',
    ],
    'assets': {
        'web.assets_frontend': [
            '/b_portal_base_l10n_mx/static/src/js/import_xml_portal.js',
        ],
    },

    'data': [
        'security/ir.model.access.csv',

        'views/res_config_settings_view.xml',
        'views/inherit_portal_my_purchase_orders.xml',
        'views/inherited_account_views.xml',
        'views/inherit_account_tax.xml',
        'views/inherited_l10n_mx_edi_views.xml',

        'wizard/import_xml_wizard.xml',
        'wizard/import_zip_xml_wizard.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False
}
