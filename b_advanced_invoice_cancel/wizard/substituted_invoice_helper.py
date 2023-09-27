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
from odoo import models, fields, _
from odoo.exceptions import ValidationError


class SubstitutedInvoiceHelper(models.TransientModel):
    _name = 'substituted.invoice.helper'
    _description = 'Helper model to help to created substituted from out/refund invoices'

    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice origin',
        required=True,
        help='This is the invoice from a substituted invoice will be created'
    )

    def create_substituted_invoice(self):
        """
            :return: Returns a substituted invoice which has been created from the origin invoice.
        """
        if not self.invoice_id:
            raise ValidationError(
                _('Was not possible to create the substituted invoice, due to '
                  'the origin invoice was not found, close the assistant and try it again.'))
        if not self.invoice_id.l10n_mx_edi_cfdi_uuid:
            raise ValidationError(
                _('Was not possible to create the substituted invoice, due to '
                  'the origin invoice SAT status is not valid. A valid SAT status is required '
                  'to create a substituted invoice.'))
        # we include businness fields, like sale_line_ids, in order to keep the
        # invoiced_qty updated, due to this invoiced is being substituted the current
        # invoiced and it has to affect the sale order.
        move_vals = self.invoice_id.with_context(
            include_business_fields=True).copy_data(
                {'date': self.invoice_id.date or fields.Date.context_today(self)})[0]
        move_vals.update({
            'is_substitution_invoice': True,
            'origin_invoice_id': self.invoice_id.id,
            'l10n_mx_edi_origin': '04|{}'.format(self.invoice_id.l10n_mx_edi_cfdi_uuid),
        })
        res_id = self.env['account.move'].create(move_vals)
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        action['context'] = dict(self.env.context)
        action['context']['form_view_initial_mode'] = 'edit'
        action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
        action['res_id'] = res_id.id
        return action
