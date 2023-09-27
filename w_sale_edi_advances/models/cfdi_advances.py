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
from odoo import api, fields, models


class CfdiAdvances(models.Model):
    _name = 'cfdi.advances'
    _description = 'Records for invoices advances'

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Gives the sequence of this line when displaying.'
    )

    invoice_id = fields.Many2one(
        'account.move',
        ondelete='cascade'
    )

    advance_id = fields.Many2one(
        'account.move',
        string='Invoice related',
        help='This field stores the invoices of the advance type related'
             'to the fiscal folio'
    )

    folio_fiscal = fields.Char(
        related='advance_id.l10n_mx_edi_cfdi_uuid',
        string='Fiscal folio',
        readonly=True,
        help='This field stores the fiscal folio corresponding to the'
             'invoice'
    )

    currency_id = fields.Many2one(
        'res.currency',
        related='advance_id.currency_id'
    )
    
    amount_total = fields.Monetary(
        string='Amount',
        related='advance_id.amount_untaxed',
        currency_field='currency_id',
        readonly=True,
        help='This field stores the total corresponding to the advance'
    )
