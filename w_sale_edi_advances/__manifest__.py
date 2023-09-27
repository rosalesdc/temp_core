# -*- encoding: utf-8 -*-
#
# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2022 Birtum - https://www.birtum.com
# All Rights Reserved.
#
# Developer(s): Eddy Luis Pérez Vila
#               epv@birtum.com
#########################################################
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
#########################################################

{
    'name': 'Wedoo | Edi Advances CFDI',
    'author': 'Wedoo ©',
    'category': 'Accounting',
    'sequence': 50,
    'summary': "EDI CFDI Advances",
    'website': 'https://www.wedoo.tech',
    'version': '15.0',
    'description': """
Advances CFDI
=========================
This module relates the advance invoices generated from a sales order to
the final invoice of the order, when the option to deduct advances is
chosen, it adds the necessary discount to the lines according to the total
of advances generated from the sales order.
""",
    'depends': [
        'base',
        'account',
        'account_accountant',
        'account_edi',
        'sale',
        'sale_management',
        'l10n_mx',
        'l10n_mx_edi',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/inherit_sale_order_view.xml',
        'views/inherit_account_move_view.xml',
        'wizard/inherit_sale_advance_payment_view.xml',
    ],
    'installable': True,
    'application': False,
}
