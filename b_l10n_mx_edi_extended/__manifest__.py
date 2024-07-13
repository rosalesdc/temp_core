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
    'name': 'BIRTUM | MX EDI Extended.',
    'author': 'BIRTUM ©',
    'category': 'Accounting/Localizations/EDI',
    'sequence': 50,
    'summary': """Adds new features for MX EDI 40.""",
    'website': 'https://www.birtum.com',
    'version': '16.2.1.3',
    'last_update': '17-02-2024',
    'description': """
BIRTUM | BIRTUM | MX EDI Extended.

This module contains extensions for the Mexican localization.
""",
    'depends': [
        'base',
        'account',
        'l10n_mx_edi',
        'l10n_mx_edi_40', 
    ],
    'data': [
        # TODO
        # comment the report due to it is not required for PERFILES Y ACEROS
        # 'report/inherit_report_invoice_document.xml',
        'views/inherit_account_move_view.xml'
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
