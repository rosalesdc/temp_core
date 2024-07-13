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
    'name': 'BIRTUM | Fast Invoicing',
    'author': 'BIRTUM ©',
    'category': 'Website',
    'sequence': 50,
    'summary': """ Invoicing from website""",
    'website': 'https://www.birtum.com',
    'license': 'OPL-1',
    'version': '16.0.1',
    'description': """
        Search and invoice PoS orders from website.
    """,
    
    'depends': [
        'analytic',
        'website',
        'sale_stock',
        'sale_management',
        'point_of_sale',
        'l10n_mx_edi'
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
        # SECURITY
        'security/ir.model.access.csv',
        'security/fast_invoicing_security.xml',
        # DATA
        'data/website_data.xml',
        'data/cfdi.xml',
        'data/payment10.xml',
        # VIEWS
        'views/inherit_res_config_settings_view.xml',
        'views/inherit_orders_views.xml',
        'views/inherit_account_analytic_account_views.xml',
        'views/account_payment_manual_views.xml',
        'views/ir_actions_server.xml',
        'views/account_invoice_view.xml',
        'views/inherit_account_payment_views.xml',
        'views/pos_payment_method_view.xml',
        "views/inherit_view_pos_order_tree.xml",
        # REPORTS
        'report/report_invoice.xml',
        # TEMPLATE
        'views/website_invoicing_templates.xml',
    ],
    'qweb': [
    ],
    'demo': [
    ],
    'installable': True,
    'application': False,
}
