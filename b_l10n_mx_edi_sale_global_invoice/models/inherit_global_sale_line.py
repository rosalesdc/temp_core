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
from odoo import models, fields, api, _
from collections import defaultdict
from odoo.exceptions import UserError


class GlobalInvoiceLine(models.Model):
    _inherit = 'global.invoice.line'

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale order',
        copy=False,
        help='The sale order were the global invoice line was created',
    )
    l10n_mx_edi_global_sale_line_ids = fields.Many2many(
        'sale.order.line',
        string='Sale order lines'
    )

    @api.depends('tax_ids', 'l10n_mx_edi_global_sale_line_ids')
    def _global_taxes(self):
        """
            compute method to validate if the pos order related to the invoice line
            has taxes.
        """
        super(GlobalInvoiceLine, self)._global_taxes()
        for line in self:
            sale_line_taxes = line.l10n_mx_edi_global_sale_line_ids.mapped('tax_id')
            if sale_line_taxes:
                line.has_global_taxes = True
                continue

    @api.depends(
        'l10n_mx_edi_global_sale_line_ids',
        'has_global_taxes',
    )
    def _compute_sale_global_taxes(self):
        super(GlobalInvoiceLine, self)._compute_sale_global_taxes()
        for line in self:
            if line.has_global_taxes and line.l10n_mx_edi_global_sale_line_ids:
                base_line_vals_list = []
                sign = 1
                grouped_taxes = {
                    'tax_details': defaultdict(lambda: {
                        'base_amount_currency': 0.0,
                        'base_amount': 0.0,
                        'tax_amount_currency': 0.0,
                        'tax_amount': 0.0,
                    })
                }
                for sale_line in line.l10n_mx_edi_global_sale_line_ids:
                    account = line.product_id._get_product_accounts()['income']
                    if not account:
                        raise UserError(_(
                            "Please define income account for this product: '%s' (id:%d).",
                            line.product_id.name, line.product_id.id,
                        ))

                    if line.move_id.fiscal_position_id:
                        account = line.move_id.fiscal_position_id.map_account(account)

                    base_line_vals_list.append(sale_line._convert_to_tax_base_line_dict())
                tax_results = self.env['account.tax']._compute_taxes(base_line_vals_list)
                if len(tax_results['tax_lines_to_add']) > 0:
                    for tax in tax_results['tax_lines_to_add']:
                        key = tax['tax_id']
                        if key not in grouped_taxes['tax_details']:
                            tax_id = self.env['account.tax'].browse(key)
                            grouped_taxes['tax_details'][key] = {
                                'tax': tax_id,
                                'base_amount': (tax['base_amount'] * sign),
                                'tax_amount': (tax['tax_amount'] * sign),
                                'base_amount_currency': (tax['base_amount_currency'] * sign),
                                'tax_amount_currency': (tax['tax_amount_currency'] * sign),
                                'tax_rate_transferred': line.move_id._get_tax_type(tax_id, tax),
                                'group_tax_details': tax['group_tax_details']
                            }
                        else:
                            grouped_taxes['tax_details'][key].update({
                                'base_amount': grouped_taxes['tax_details'][key]['base_amount'] + (tax['base_amount'] * sign),
                                'tax_amount': grouped_taxes['tax_details'][key]['tax_amount'] + (tax['tax_amount'] * sign)
                            })
                line.sale_grouped_taxes = grouped_taxes
