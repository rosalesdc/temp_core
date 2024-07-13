#########################################################
# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2023 Birtum - https://www.birtum.com
# All Rights Reserved.
#
# Developer(s): Eddy Luis Pérez Vila <epv@birtum.com>
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
    "name": "BIRTUM | Administrador de documentos digitales",
    "description": """
        Descarga los CFDI del portal del SAT a la base de datos de
        Odoo para su procesamiento y administración, se necesita de la librería de python
        xmltodict - sudo pip3 install xmltodict
        OpenSSL - sudo apt-get install python3-openssl
    """,
    "category": "Accounting",
    "author": "BIRTUM ©",
    "website": "https://www.birtum.com",
    "version": "16.1.4.6",
	'last_update': '12-06-2024',
    "depends": [
        "account",
        "account_accountant",
        "l10n_mx_edi",
        "purchase",
    ],
    "data": [
        # DATA
        "data/data_operation_type.xml",
        "data/masive_sat.xml",
        # SECURITY
        "security/sat_documents_groups.xml",
        "security/ir.model.access.csv",
        # VIEWS
        "views/account_move_views.xml",
        "views/account_tax_views.xml",
        "views/res_company_view.xml",
        "views/res_config_settings_view.xml",
        "views/sat_documents_views.xml",
        # WIZARDS
        "wizards/sat_documents_range_download_views.xml",
    ],
    "application": False,
    "installable": True,
    "license": "AGPL-3",
}
