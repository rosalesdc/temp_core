# -*- encoding: utf-8 -*-
#
# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2024 Birtum - https://www.birtum.com
# All Rights Reserved.
#
# Developer(s): Alan Guzmán
#               age@birtum.com
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
    'name': 'BIRTUM | Sale global invoice MX EDI',
    'author': 'BIRTUM ©',
    'category': 'Accounting/Localization/EDI',
    'summary': 'Sale global invoice',
    'website': 'https://www.birtum.com',
    'last_update': '29-02-2024',
    'version': '16.2.0.2',
    'description': """
BIRTUM | Sale global invoice MX EDI
------------------------------------------
    """,
    'depends': [
        'base',
        'account',
        'sale',
        'sales_team',
        'b_l10n_mx_edi_global_invoice'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/inherit_account_move_view.xml',
        'views/inherit_sale_order_view.xml',
        'wizard/sale_make_global_invoice_view.xml'
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
