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
from odoo import models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def get_tax_code(self):
        """
            tool method to return the code of a tax
            Returns:
                dict: return a code of a tax
        """
        return lambda t: {'ISR': '001', 'IVA': '002', 'IEPS': '003'}.get(t, '')

    def get_invoice_taxes(self):
        """
            tool method to return all the applied taxes to an invoice
            Returns:
                dict: array of taxes
        """
        tax_details_transferred = self._prepare_edi_tax_details()
        return tax_details_transferred

    @api.model
    def get_amount_tax_line(self, tax_details, inv_line):
        """
            tool method to sum all the amount taxes of a invoice line
            Args:
                tax_details (dict): dict with taxes vals
                inv_line (object): a record of account.move.line

            Returns:
                float: the total amount applied to an invoice line
        """
        taxes_line = tax_details['tax_details_per_record'][inv_line]['tax_details']
        tax_amount = sum([tax['tax_amount'] for tax in taxes_line.values()])
        return tax_amount
