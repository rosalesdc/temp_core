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
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.osv import expression


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_there_advances = fields.Boolean(
        compute='check_invoice_advances',
        help='Tehcnical field to validate whether the sales order has advances.'
    )

    @api.depends(
        'invoice_ids', 'invoice_ids.is_advance',
        'invoice_ids.advance_related', 'invoice_ids.l10n_mx_edi_cfdi_uuid',
        'invoice_ids.l10n_mx_edi_sat_status', 'invoice_ids.state')
    def check_invoice_advances(self):
        """
            Looking for invoice advances related to the sales orders.
        """
        for sale in self:
            sale.is_there_advances = True if sale.get_advance_invoices() else False
    
    def get_advance_invoices(self):
        """
            Advances have to meet the following conditions:
            is_advance: in True
            advance_related in False
            Having a value at l10n_mx_edi_cfdi_uuid field
            State in posted
            l10n_mx_edi_sat_status is valid.
        """
        self.ensure_one()
        invoice_ids = self.invoice_ids.filtered(
            lambda l: l.is_advance and not l.advance_related
            and l.l10n_mx_edi_cfdi_uuid and l.l10n_mx_edi_sat_status == 'valid'
            and l.state == 'posted')
        # invoice_ids = self.invoice_ids.filtered(
        #     lambda l: l.is_advance and not l.advance_related
        #               and l.state == 'posted')
        return invoice_ids

    def _create_invoices(self, grouped=False, final=False, date=None):
        """
            Inheritance to remove negative lines and apply this logic:
            - If final(deduct_down_payments): we apply the advance percentage to each
                invoice line.
        """
        amount_total_advances = 0.0
        advance_values = []
        account_invoice_ids = super(SaleOrder, self)._create_invoices(
            grouped=grouped, final=final, date=date)
        if self._context.get('advances', False):
            advances = self._context.get('advances', [])
            for inv in account_invoice_ids:
                # The remove process will done using this technique because we
                # need that invoice recompute move lines automatically to avoid
                # unbalanced move(invoice)
                if final:
                    if not advances:
                        raise UserError(_('Advance invoice are required to deduct values'))
                    lines_to_invoice = inv.invoice_line_ids.filtered(
                        lambda line: line.sale_line_ids.filtered(
                        lambda sale_line: not sale_line.is_downpayment))
                    for inv_line in lines_to_invoice:
                        line_qty = {'quantity': abs(inv_line.quantity)}
                        inv_line.with_context(check_move_validity=False).write(line_qty)
                    inv.write({'invoice_line_ids': [(5, 0, 0)] + [(6, 0, lines_to_invoice.ids)]})
                    final_no_advances = False
                    inv.invoice_line_ids.with_context(
                        check_move_validity=False)._onchange_price_subtotal()
                    inv.with_context(check_move_validity=False)._recompute_dynamic_lines(
                        recompute_all_taxes=True)
                    total_amount = inv.amount_total
                    # we calculate the sum of amount advances
                    for advance in advances:
                        amount_total_advances += advance.amount_total
                        advance_values.append(self.prepare_advance_values(inv.id, advance.id))
                    if amount_total_advances > 0 and inv.invoice_line_ids:
                        percent_advance = self.get_advance_percent(amount_total_advances, total_amount)
                        for line_id in inv.invoice_line_ids.filtered(lambda x: not x.display_type):
                            # we assume that the invoice line has a discount and then we
                            # apply the discount from advances to the price_subtotal and finally
                            # we divide the result among the quantity
                            # price_wh_advance = line_id.price_subtotal * (1 - (percent_advance / 100))
                            # price_unit = price_wh_advance / line_id.quantity
                            line_id.with_context(check_move_validity=False).write(
                                {'discount': percent_advance})
                            line_res = self.env['account.move.line']._get_price_total_and_subtotal_model(
                                    line_id.price_unit,
                                    line_id.quantity,
                                    percent_advance,
                                    line_id.currency_id,
                                    line_id.product_id,
                                    line_id.partner_id,
                                    line_id.tax_ids,
                                    line_id.move_id.move_type)
                            line_id.with_context(check_move_validity=False).write(line_res)
                    inv.invoice_line_ids.with_context(
                        check_move_validity=False)._onchange_price_subtotal()
                    inv.with_context(check_move_validity=False)._recompute_dynamic_lines(
                        recompute_all_taxes=True)
                else:
                    final_no_advances = True
                    for adv in advances:
                        advance_values.append(self.prepare_advance_values(inv.id, adv.id))
                if advance_values:
                    self.env['cfdi.advances'].create(advance_values)
                if inv.advance_ids:
                    inv.relate_advances = True
                    inv.action_relate_fiscal_folio()
                    inv.final_no_advances = final_no_advances
                    inv.is_final = True
        return account_invoice_ids

    @api.model
    def get_advance_percent(self, amount_advance, total_amount):
        """
            returns the percentage to each invoice line.
        """
        return (amount_advance / total_amount) * 100

    # return a dict to create a registry in cfdi.advances
    @api.model
    def prepare_advance_values(self, invoice_id, advance_id):
        """
            returns a dict to create a registry in cfdi.advances
        """
        return {
            'sequence': 10,
            'advance_id': advance_id,
            'invoice_id': invoice_id,
            }

    @api.depends('order_line.invoice_lines')
    def _get_invoiced(self):
        """
            Inheritance to add refunds to sale invoices. Base method only show
            regular invoices, we take them from advance_ids of invoice_ids.
        """
        super(SaleOrder, self)._get_invoiced()
        for order in self:
            # Search for refunds as well
            domain_inv = expression.OR([
                ['&', ('invoice_origin', '=', inv.name),
                 ('journal_id', '=', inv.journal_id.id)]
                for inv in order.invoice_ids if inv.name
            ])
            if domain_inv:
                refund_ids = self.env['account.move'].search(expression.AND([
                    ['&', ('move_type', '=', 'out_refund'),
                     ('invoice_origin', '!=', False)],
                    domain_inv
                ]))
                order.invoice_ids |= refund_ids
                order.invoice_count += len(refund_ids)
