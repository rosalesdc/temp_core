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
    'name': 'BIRTUM | Manual group account',
    'author': 'BIRTUM ©',
    'category': 'CRM',
    'sequence': 50,
    'summary': "Manual group account",
    'website': 'https://www.birtum.com',
    'version': '16.1.1.2',
    'last_update': '05-06-2024',
    'license': 'AGPL-3',
    'description': """
Manual group account
===============================================================
    """,
    'depends': [
        'base',
        'account',
        'l10n_mx_reports',
    ],
    'data': [
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': False,
}
