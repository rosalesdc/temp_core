# -*- encoding: utf-8 -*-
#
# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2022 Birtum - https://www.birtum.com
# All Rights Reserved.
#
# Developer(s): Alan Guzmán
#               age@wedoo.tech
######################################################################
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
    'name': 'BIRTUM | Advanced invoice EDI cancellation',
    'author': 'BIRTUM ©',
    'category': 'Accounting',
    'sequence': 50,
    'summary': "Advanced invoice cancel",
    'website': 'https://www.birtum.com',
    'version': '15.0',
    'description': """
Advanced invoice cancel
===============================================================
This module adds extra features for EDI cancellation, in order to improve it,
when the EDI document is cancelled by SAT, a reversal invoice is created, it is
related to the current invoiced.
""",
    'depends': [
        'base',
        'account',
        'sale',
        'l10n_mx_edi'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/inherit_account_move_view.xml',
        'wizard/substituted_invoice_helper_view.xml'
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
