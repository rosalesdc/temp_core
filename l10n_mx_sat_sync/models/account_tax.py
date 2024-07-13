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
##########################################################
from odoo import fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    l10n_mx_tax_code = fields.Selection(
        selection=[
            ("001", "ISR"),
            ("002", "IVA"),
            ("003", "IEPS"),
        ],
        string="Tax code",
        default="002",
        help="The CFDI version 3.3/4.0 have the attribute Impuesto in the tax lines. In it is indicated the tax "
        "that is applied to the base of the tax.",
    )
