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
from odoo import models, fields, api, exceptions, SUPERUSER_ID, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    invoiced = fields.Boolean(
        string='Facturado',
        readonly=True,
        copy=False,
        help='Este campo toma valor desde el portal de proveedor, cuando se carga '
             'un comprobante CFDI al albaran.'
    )
    vat_emisor = fields.Char(
        string='RFC Emisor',
        related='partner_id.vat',
        readonly=True,
    )
    vat_receptor = fields.Char(
        string='RFC Receptor',
        related='company_id.vat',
        readonly=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        'company_id.currency_id'
    )
    # cfdi_amount_total = fields.Float(
    #     string='Valor total',
    #     compute='_get_amount_total',
    # )
    # cfdi_tax_codes = fields.Char(
    #     string='Código del impuesto SAT',
    #     compute='_get_amount_total',
    # )
    invoice_ids = fields.One2many(
        'account.move',
        'stock_picking_id',
        help='Las facturas creadas desde el portal de proveedores que nacen desde '
             'el albaran.'
    )

    # @api.depends('purchase_id', 'move_lines', 'move_lines.purchase_line_id')
    # def _get_amount_total(self):
    #     """
    #         computed method to get the tax sat codes from purchase order line and
    #         the amount total for the qty received of of the purchase order lines,
    #         related to the picking.
    #     """
    #     for picking in self:
    #         purchase_line_ids = picking.move_lines.mapped('purchase_line_id')
    #         amount_total = sum([self._get_price_total_qty_received(line) for line in purchase_line_ids])
    #         tax_ids = purchase_line_ids.mapped('taxes_id')
    #         tax_sat_codes = ','.join(tax_ids.filtered(lambda x: x.tax_sat_code).mapped('tax_sat_code'))
    #         picking.cfdi_tax_codes = tax_sat_codes
    #         picking.cfdi_amount_total = amount_total

    @api.model
    def _get_price_total_qty_received(self, purchase_line_id):
        taxes = purchase_line_id.taxes_id.compute_all(
            purchase_line_id.price_unit, purchase_line_id.currency_id,
            purchase_line_id.qty_received, purchase_line_id.product_id,
            purchase_line_id.order_id.partner_id)
        return taxes['total_included']

    @api.model
    def check_invoiced(self, pickid):
        if pickid:
            pick = self.with_user(SUPERUSER_ID).browse(int(pickid))
            return {'invoiced': pick.invoiced if len(pick) else False}
        raise exceptions.ValidationError(_('Yo must provide a stock pincking'))
