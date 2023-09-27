# -*- encoding: utf-8 -*-
#
# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2022 Birtum - https://www.birtum.com
# All Rights Reserved.
#
# Developer(s): Alan Guzmán
#               age@wedoo.tech
######################################################################
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
from odoo.osv import expression


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('order_line.invoice_lines')
    def _get_invoiced(self):
        """
            inherited method in order to extend the invoices related to the SO,
            now it includes substituted invoices related to sale order invoices.
        """
        # The invoice_ids are obtained thanks to the invoice lines of the SO
        # lines, and we also search for possible refunds created directly from
        # existing invoices. This is necessary since such a refund is not
        # directly linked to the SO.
        super(SaleOrder, self)._get_invoiced()
        for order in self:
            # Search for refunds as well
            domain_inv = expression.OR([
                ['&', ('invoice_origin', '=', order.name),
                 ('journal_id', '=', inv.journal_id.id)]
                for inv in order.invoice_ids if inv.name
            ])
            if domain_inv:
                substituted_invoices = self.env['account.move'].search(
                    expression.AND([['&', ('move_type', '=', 'out_invoice'),
                                     ('invoice_origin', '!=', False)],
                                    domain_inv])
                )
                order.invoice_ids |= substituted_invoices
                order.invoice_count = len(substituted_invoices)
