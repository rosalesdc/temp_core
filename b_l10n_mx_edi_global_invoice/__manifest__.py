# -*- encoding: utf-8 -*-
#
# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2023 Birtum - https://www.birtum.com
# All Rights Reserved.
#
# Developer(s): Alan Guzmán
#               age@wedoo.tech
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
    'name': 'BIRTUM  | Global Invoice MX EDI',
    'author': 'BIRTUM ©',
    'category': 'Accounting/Localization/EDI',
    'sequence': 50,
    'summary': """Allows to create a Global invoice EDI document.""",
    'website': 'https://www.birtum.com',
    'version': '16.3.1.4',
    'last_update': '22-02-2024',
    'description': """
BIRTUM | Global Invoice MX EDI

""",
    'depends': [
        'base',
        'account',
        'l10n_mx_edi',
        'l10n_mx_edi_40',
        'b_l10n_mx_edi_extended',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/cfdiv40.xml',
        'data/global_invoice.xml',
        'report/inherit_report_invoice_document.xml',
        'views/inherit_account_move_view.xml'
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
