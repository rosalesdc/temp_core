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
from odoo import models, fields, api
from collections import defaultdict


class AccountMoveLine(models.Model):
    _name = 'global.invoice.line'
    _description = 'Lines for concepts of global invoice'

    # TODO
    # it is required to add help to the fields
    has_global_taxes = fields.Boolean(
        string='Global taxes',
        compute='_global_taxes',
    )
    sale_grouped_taxes = fields.Binary(
        string='Grouped taxes',
        compute='_compute_sale_global_taxes',
        exportable=False,
    )
    name = fields.Char(
        string='Label'
    )
    # === Parent fields === #
    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Journal Entry',
        required=True,
        readonly=True,
        index=True,
        auto_join=True,
        ondelete="cascade",
        check_company=True,
    )
    sequence = fields.Integer(
        compute='_compute_sequence',
        store=True,
        readonly=False,
        precompute=True
    )
    move_type = fields.Selection(
        related='move_id.move_type'
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        compute='_compute_currency_id', store=True, readonly=False, precompute=True,
        required=True,
    )
    company_id = fields.Many2one(
        related='move_id.company_id', store=True, readonly=True, precompute=True,
        index=True,
    )
    company_currency_id = fields.Many2one(
        string='Company Currency',
        related='move_id.company_currency_id', readonly=True, store=True, precompute=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        ondelete='restrict',
    )
    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Unit of Measure',
    )
    tax_repartition_line_id = fields.Many2one(
        comodel_name='account.tax.repartition.line',
        string="Originator Tax Distribution Line",
        ondelete='restrict',
        readonly=True,
        check_company=True,
        help="Tax distribution line that caused the creation of this move line, if any"
    )
    tax_ids = fields.Many2many(
        comodel_name='account.tax',
        string="Taxes",
        context={'active_test': False},
        check_company=True,
    )
    tax_line_id = fields.Many2one(
        comodel_name='account.tax',
        string='Originator Tax',
        related='tax_repartition_line_id.tax_id', store=True, precompute=True,
        ondelete='restrict',
        help="Indicates that this journal item is a tax line"
    )
    quantity = fields.Float(
        string='Quantity',
        digits='Product Unit of Measure',
        help="The optional quantity expressed by this line, eg: number of product sold. "
             "The quantity is not a legal requirement but is very useful for some reports.",
    )
    # === Price fields === #
    price_unit = fields.Float(
        string='Unit Price',
        digits='Product Price',
    )
    price_subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_totals', store=True,
        currency_field='currency_id',
    )
    price_total = fields.Monetary(
        string='Total',
        compute='_compute_totals', store=True,
        currency_field='currency_id',
    )
    discount = fields.Float(
        string='Discount (%)',
        digits='Discount',
        default=0.0,
    )
    display_type = fields.Selection(
        selection=[
            ('product', 'Product'),
            ('cogs', 'Cost of Goods Sold'),
            ('tax', 'Tax'),
            ('rounding', "Rounding"),
            ('payment_term', 'Payment Term'),
            ('line_section', 'Section'),
            ('line_note', 'Note'),
            ('epd', 'Early Payment Discount')
        ],
        required=True,
    )



    @api.depends('move_id.currency_id')
    def _compute_currency_id(self):
        """
            computed method to get the currency for the global invoice lines
        """
        for line in self:
            if line.display_type == 'cogs':
                line.currency_id = line.company_currency_id
            elif line.move_id.is_invoice(include_receipts=True):
                line.currency_id = line.move_id.currency_id
            else:
                line.currency_id = line.currency_id or line.company_id.currency_id

    @api.depends('display_type')
    def _compute_sequence(self):
        """
            compute method to order the global invoice lines
        """
        seq_map = {
            'tax': 10000,
            'rounding': 11000,
            'payment_term': 12000,
        }
        for line in self:
            line.sequence = seq_map.get(line.display_type, 100)

    @api.depends('quantity', 'discount', 'price_unit', 'tax_ids', 'currency_id')
    def _compute_totals(self):
        """
            computed method to get the global amount of the global invoice lines
        """
        for line in self:
            commercial_partner = line.move_id.partner_id.commercial_partner_id
            if line.display_type != 'product':
                line.price_total = line.price_subtotal = False
            # Compute 'price_subtotal'.
            line_discount_price_unit = line.price_unit * (1 - (line.discount / 100.0))
            subtotal = line.quantity * line_discount_price_unit
            # Compute 'price_total'.
            if line.tax_ids:
                taxes_res = line.tax_ids.compute_all(
                    line_discount_price_unit,
                    quantity=line.quantity,
                    currency=line.currency_id,
                    product=line.product_id,
                    partner=commercial_partner,
                    is_refund=line.is_refund,
                )
                line.price_subtotal = taxes_res['total_excluded']
                line.price_total = taxes_res['total_included']
            else:
                line.price_total = line.price_subtotal = subtotal

    @api.depends('tax_ids')
    def _global_taxes(self):
        """
            compute method to validate if the pos order related to the invoice line
            has taxes.
        """
        for line in self:
            if line.tax_ids:
                line.has_global_taxes = True
                continue
            line.has_global_taxes = False

    @api.depends('has_global_taxes')
    def _compute_sale_global_taxes(self):
        """
            this method has to be overwritten for the app which is created
            a global invoice
        """
        for line in self:
            line.sale_grouped_taxes = None


    def _prepare_edi_global_invoice_vals_to_export(self):
        ''' 
            The purpose of this helper is the same as '_prepare_edi_vals_to_export' but for a single invoice line.
            This includes the computation of the tax details for each invoice line or the management of the discount.
            Indeed, in some EDI, we need to provide extra values depending the discount such as:
            - the discount as an amount instead of a percentage.
            - the price_unit but after subtraction of the discount.

            :return: A python dict containing default pre-processed values.
        '''
        self.ensure_one()

        if self.discount == 100.0:
            gross_price_subtotal = self.currency_id.round(self.price_unit * self.quantity)
        else:
            gross_price_subtotal = self.currency_id.round(self.price_subtotal / (1 - self.discount / 100.0))

        res = {
            'line': self,
            'price_unit_after_discount': self.currency_id.round(self.price_unit * (1 - (self.discount / 100.0))),
            'price_subtotal_before_discount': gross_price_subtotal,
            'price_subtotal_unit': self.currency_id.round(self.price_subtotal / self.quantity) if self.quantity else 0.0,
            'price_total_unit': self.currency_id.round(self.price_total / self.quantity) if self.quantity else 0.0,
            'price_discount': gross_price_subtotal - self.price_subtotal,
            'price_discount_unit': (gross_price_subtotal - self.price_subtotal) / self.quantity if self.quantity else 0.0,
            'gross_price_total_unit': self.currency_id.round(gross_price_subtotal / self.quantity) if self.quantity else 0.0,
            'unece_uom_code': self.product_id.product_tmpl_id.uom_id._get_unece_code(),
        }
        return res
