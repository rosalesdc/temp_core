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
from odoo import api, models, _, fields
from odoo.exceptions import UserError


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    @api.model
    def _check_advance_invoices_to_deduct(self):
        """
            checking if the sales orders has advances invoices
        """
        if self._context.get('active_model') == 'sale.order' and self._context.get('active_id', False):
            sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
            return any(sale_orders.mapped('is_there_advances'))
        return False

    has_downpayments_to_deduct = fields.Boolean(
        string='Has downpayments to deduct',
        default=_check_advance_invoices_to_deduct,
        readonly=True,
        help='Technical field to check if the sales orders has advances invoices',
    )

    lines_to_invoice = fields.Boolean(
        default=lambda self: bool(self.get_lines_to_invoice()),
        help='Validate if the sales order has line to be invoiced.'
    )

    total_amount_lines = fields.Float(
        compute='get_amount_lines',
        help='Computes the total amount of the sales order to be invoiced.'
    )

    total_amount_advances = fields.Float(
        compute='get_amount_advances',
        help='Computes the total amount of the related advances of the sales order.'
    )

    advance_ids = fields.One2many(
        'sale.advance.inv',
        'sale_advance_id',
        default=lambda self: self.get_invoices_advances(),
        help='Gets the advances related to the sales order.'
    )

    @api.onchange('advance_payment_method', 'deduct_down_payments')
    def onchange_advance_payment_method(self):
        """
            Fills advance invoice field based on advanced invoices from sale order.
            By the time only show advance lines that amount_total is lower than
            current sale order amount_total
        """
        result = super(SaleAdvancePaymentInv, self).onchange_advance_payment_method()
        result.setdefault('value', {})
        if self.advance_payment_method == 'delivered' and self.has_downpayments_to_deduct:
            advance_ids = self.get_advances()
            advances = [(5, 0, 0)]
            if advance_ids:
                amount_lines = self.total_amount_lines
                for advance in advance_ids:
                    if advance.amount_untaxed < amount_lines:
                        advances.append(
                            (0, 0, {
                                'invoice_id': advance.id,
                                'use_advance': True,
                                }))
                result['value']['advance_ids'] = advances
        else:
            result['value']['advance_ids'] = [(5, 0, 0)]
        return result

    @api.depends('advance_ids')
    def get_amount_advances(self):
        """
            Computes sum of amount_advance from all invoices mark as use_advance
        """
        self.total_amount_advances = sum(self.advance_ids.filtered(
            lambda l: l.use_advance == True).mapped('amount_advance'))

    @api.depends('lines_to_invoice')
    def get_amount_lines(self):
        """
            Compute sum of amount total from all invoiceable lines
        """
        self.total_amount_lines = sum(self.get_lines_to_invoice().mapped(
            lambda x : x.qty_to_invoice * x.price_unit))

    def get_lines_to_invoice(self):
        """
            Search and returns sale order lines that:
            - product_id is different than Deposit Product of sale configuration(not is_downpayment)
        """
        sale_orders = self.env['sale.order'].browse(
            self._context.get('active_ids')
        )
        sale_lines = self.env['sale.order.line']
        for order in sale_orders:
            sale_lines += order.mapped('order_line').filtered(
                lambda l: l.invoice_status == 'to invoice'
                and not l.is_downpayment
                and l.display_type == False)
        return sale_lines

    def get_advances(self):
        """
            Search advanced invoices in sale order to show in wizard. Advance
            invoices must have this requirements:
            - is_advance field in True
            - advance_related in False
            - Have l10n_mx_edi_cfdi_uuid
            - State in posted
            - l10n_mx_edi_sat_status is valid.
        """
        advances = []
        for order in self.env['sale.order'].browse(self._context.get('active_ids')):
            advances += order.invoice_ids.filtered(
                lambda l: l.is_advance and not l.advance_related
                and l.l10n_mx_edi_cfdi_uuid and l.l10n_mx_edi_sat_status == 'valid'
                and l.state == 'posted')
            # advances += order.invoice_ids.filtered(
            #     lambda l: l.is_advance and not l.advance_related
            #     and l.l10n_mx_edi_cfdi_uuid and l.l10n_mx_edi_sat_status == 'valid'
            #     and l.state == 'posted')
        return advances

    def get_invoices_advances(self):
        """
            Build advanced dictionaries to show in wizard. Base data has taken from
            get_advances
        """
        advance_ids = self.get_advances()
        advances = []
        if advance_ids:
            for advance in advance_ids:
                if advance.amount_untaxed < self.total_amount_lines:
                    advances.append((0, 0, 
                        {
                            'use_advance': True,
                            'invoice_id': advance.id,
                        }))
        return advances

    def _create_invoice(self, order, so_line, amount):
        """
            Inheritance to mark advance invoices
        """
        res = super(SaleAdvancePaymentInv, self)._create_invoice(order, so_line, amount)
        res.write(
            {
                'is_advance': True,
                'advance_from_sale': True,
            })
        return res

    def create_invoices(self):
        """
            Inheritance to add some validations in create invoice process
        """
        if self.advance_payment_method == 'delivered':
            if self.deduct_down_payments and self.has_down_payments and self.has_downpayments_to_deduct:
                if self.total_amount_lines <= 0:
                    raise UserError(_(
                        'You can not create an invoice by deducting advances '
                        'because there is not nothing to invoicing.')
                    )
                elif not self.advance_ids:
                    raise UserError(_(
                        'You can not create an invoice by deducting advances '
                        'because not advances.')
                    )
                elif not any(line.use_advance for line in self.advance_ids):
                    raise UserError(_('Select at least one down payment.'))
                elif self.total_amount_advances > self.total_amount_lines:
                    raise UserError(_(
                        'You can not create an invoice by deducting advances '
                        'because the amount to deduct is higher than amount '
                        'to invoice.')
                    )
                elif self.total_amount_lines == self.total_amount_advances:
                    raise UserError(
                        _('You cant create an invoice by deduction advances '
                          'because the amount to invoice is the same than '
                          'advances amount. If you want to deduct advances '
                          'you should to select advances that it doesnt passt '
                          'the amount total to invoice or you can unmark the field '
                          'deduct advances and create a regular invoice.'))
                advance_ids = self.advance_ids.filtered(
                    lambda line: line.use_advance
                ).mapped('invoice_id')
                self_context = self.with_context(advances=advance_ids)
            elif self.has_downpayments_to_deduct:
                advance_ids = self.advance_ids.filtered(
                    lambda line: line.use_advance
                ).mapped('invoice_id')
                self_context = self.with_context(advances=advance_ids)
            else:
                self_context = self
        else:
            self_context = self
        return super(SaleAdvancePaymentInv, self_context).create_invoices()


class SaleAdvanceInv(models.TransientModel):
    _name = 'sale.advance.inv'

    use_advance = fields.Boolean(
        string='Use advance',
        default=False,
        help='Mark this field in order to relate it to the final invoice.'
    )

    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        help='The ID of the advance(invoice).',
    )

    currency_id = fields.Many2one(
        'res.currency',
        related='invoice_id.currency_id'
    )

    amount_advance = fields.Monetary(
        string='Amount',
        related='invoice_id.amount_untaxed',
        currency_field='currency_id',
        help='The untaxed amount of the advance.'
    )

    sale_advance_id = fields.Many2one(
        'sale.advance.payment.inv'
    )
