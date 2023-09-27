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
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_advance = fields.Boolean(
        string='Is advance',
        default=False,
        copy=False,
        help='Indicates if the invoice is an advance'
    )
    advance_from_sale = fields.Boolean(
        default=False,
        copy=False,
        help='Indicates if the advance invoice was created from a sale order '
             'if it is then the field is advances will be readonly.'
    )
    advance_related = fields.Boolean(
        copy=False,
        help='Indicates if the advance invoice has been related to a final invoice at the time '
             'the final invoice is signed.'
    )
    relate_advances = fields.Boolean(
        string='Relate advances',
        default=False,
        copy=False,
        help='When an invoice is created from a sale order and it has related advances '
             'this field will be True.'
    )
    is_refund = fields.Boolean(
        default=False,
        copy=False,
        help='This field will be True when a final invoice has been created without related advances '
             'in this case we have to create a refund invoice which will have advances related.'
    )
    is_final = fields.Boolean(
        default=False,
        copy=False,
        hlep='Indicates if the invoice has related advances to deduct.'
    )
    final_no_advances = fields.Boolean(
        default=False,
        copy=False,
        help='Indicates that is the final invoice but without related advances.'
    )
    advance_ids = fields.One2many(
        'cfdi.advances',
        'invoice_id',
        copy=False,
        help='The related advances which will be include in the CFDI.'
    )
    total_advances = fields.Monetary(
        string='Deduction advance',
        compute='_compute_total_advances',
        help='Amount total for advances deduction.'
    )
    show_button_related = fields.Boolean(
        compute='check_all_invoice_refund',
        help='Once this invoice is signed and the refund invoice was created '
             'you can related the fiscal folio to the refund invoice, this field will be '
             'if this invoice has a refund invoice related.'
    )
    related_advances = fields.Binary(
        compute='_get_all_related_advances',
        help='Storage the ids of the advances invoices which have been related to this invoice '
             'in order to not duplicate them.'
    )

    def action_relate_fiscal_folio(self):
        """
            get the fiscal folio from related lines and set on move in cfdi origin
        """
        for move in self:
            uuids = move.advance_ids.filtered(lambda l: l.folio_fiscal).mapped('folio_fiscal')
            if len(uuids) > 0:
                move.l10n_mx_edi_origin = move._l10n_mx_edi_write_cfdi_origin('07', uuids)

    @api.depends('advance_ids', 'advance_ids.advance_id')
    def _get_all_related_advances(self):
        """
            creates an array with all invoices added to advance_ids
        """
        for move in self:
            move.related_advances = move.advance_ids.mapped('advance_id').ids

    @api.depends(
        'final_no_advances',
        'is_final',
        'l10n_mx_edi_sat_status',
        'l10n_mx_edi_cfdi_uuid',
        'state')
    def check_all_invoice_refund(self):
        """
            Looking for customer refund invoices that have been created when the invoice
            was published, if we found at least one then we show the button which related
            the fiscal folio to the refund invoices which has been found.
        """
        for inv in self:
            if inv.final_no_advances and inv.is_final and inv.l10n_mx_edi_sat_status == 'valid' and inv.l10n_mx_edi_cfdi_uuid and inv.state == 'posted':
                value_to_check = '07|{}'.format(inv.l10n_mx_edi_cfdi_uuid)
                invoice_refund_ids = self.env['account.move'].search(
                    [
                        ('reversed_entry_id', '=', inv.id),
                        ('move_type', '=', 'out_refund'),
                        ('is_refund', '=', True),
                        ('state', '=', 'draft')])
                if all(refund.l10n_mx_edi_origin == value_to_check for refund in invoice_refund_ids):
                    inv.show_button_related = False
                else:
                    inv.show_button_related = True
            else:
                inv.show_button_related = False

    def related_folio_to_rectificative(self):
        """
            Looking for the out refund invoices related to the invoice,
            we put the fiscal folio on them with code 07|
        """
        for inv in self:
            rec_ids = self.env['account.move'].search(
                [('reversed_entry_id', '=', inv.id),
                 ('move_type', '=', 'out_refund'),
                 ('is_refund', '=', True)])
            for rec in rec_ids:
                rec.l10n_mx_edi_origin = rec._l10n_mx_edi_write_cfdi_origin('07', [inv.l10n_mx_edi_cfdi_uuid])

    @api.model
    def get_default_product_id(self):
        """
            Search default deposit product from sale config and test its existence
        """
        product = self.env['ir.config_parameter'].sudo().get_param(
            'sale.default_deposit_product_id')
        product_id = self.env['product.product'].browse(int(product)).exists()
        if not product_id:
            vals = self.env['sale.advance.payment.inv'].sudo()._prepare_deposit_product()
            product_id = self.env['product.product'].create(vals)
            self.env['ir.config_parameter'].sudo().set_param(
                'sale.default_deposit_product_id', product_id.id)
        return product_id

    @api.onchange('is_advance')
    def _check_product_advance_lines(self):
        """
            creates an invoice line with down payment product
        """
        product_advance = self.get_default_product_id()
        if self.is_advance and self.state == 'draft':
            partner_id = self.partner_id
            line_values = self.prepare_advance_line_values(product_advance)
            self.with_context(check_move_validity=False).write({'invoice_line_ids': line_values})
            self.invoice_line_ids.with_context(check_move_validity=False)._onchange_price_subtotal()
            self.with_context(check_move_validity=False)._recompute_dynamic_lines(recompute_all_taxes=True)
            self.partner_id = partner_id
        else:
            keep_line_ids = self.invoice_line_ids.filtered(
                lambda rec: rec.product_id.id != product_advance.id)
            self.with_context(check_move_validity=False).write({'invoice_line_ids': [(5, 0, 0)] + [(6, 0, keep_line_ids.ids)]})
            self.invoice_line_ids.with_context(check_move_validity=False)._onchange_price_subtotal()
            self.with_context(check_move_validity=False)._recompute_dynamic_lines(recompute_all_taxes=True)

    def get_default_deposit_account_id(self):
        """
           Returns income account from default deposit product
        """
        product_id = self.get_default_product_id()
        account_id = product_id.property_account_income_id or product_id.categ_id.property_account_income_categ_id
        return account_id

    def prepare_advance_line_values(self, product_id):
        """
            prepare invoice line values
        """
        return [(0, 0, {
            'product_id': product_id.id,
            'name': product_id.name,
            'product_uom_id': product_id.uom_id.id,
            'price_unit': product_id.lst_price,
            'quantity': 1.0,
        })]

    #return total amount of advances
    # debit
    def invoice_line_move_total_advance(self):
        """
            Create vals dict to create move line that holds deduction amount
        """
        self.ensure_one()
        move_line_obj = self.env['account.move.line']
        account_id = self.get_default_deposit_account_id()
        total_advances = abs(self.total_advances)
        vals = move_line_obj._get_fields_onchange_subtotal_model(
            total_advances,
            self.move_type,
            self.currency_id,
            self.company_id,
            self.invoice_date or self.date
        )
        move_line_dict = {
            'name': _('Total Deduction advance'),
            'account_id': account_id.id,
            'partner_id': self.partner_id.id,
            'amount_currency': abs(vals.get('amount_currency', 0.0)),
            'debit': abs(vals.get('credit', 0.0)),
            'credit': 0.0,
            'currency_id': vals.get('currency_id', False),
            'move_id': self.id,
            'exclude_from_invoice_tab': True,
        }
        move_line_obj += move_line_obj.with_context(check_move_validity=False).create(move_line_dict)
        return move_line_obj

    # return an account.move.line per each line of invoice lines
    # credit
    def invoice_line_move_line_advances(self):
        """
            Create dict vals for counterpart move lines with one move line for
            invoice line and discount as credit value
        """
        self.ensure_one()
        move_line_obj = self.env['account.move.line']
        for line in self.invoice_line_ids.filtered(lambda l: not l.display_type):
            credit = (line.price_subtotal / self.amount_untaxed) * self.total_advances
            vals = move_line_obj._get_fields_onchange_subtotal_model(
                credit,
                self.move_type,
                self.currency_id,
                self.company_id,
                self.invoice_date or self.date
            )
            move_line_dict = {
                'name': _('Advances deduction'),
                'account_id': line.account_id.id,
                'partner_id': self.partner_id.id,
                'amount_currency': vals.get('amount_currency'),
                'debit': 0.0,
                'credit': abs(vals.get('credit', 0.0)),
                'currency_id': vals.get('currency_id', False),
                'move_id': self.id,
                'exclude_from_invoice_tab': True,
            }
            move_line_obj += move_line_obj.with_context(check_move_validity=False).create(move_line_dict)
        return move_line_obj

    # compute the amount of advances
    @api.depends('advance_ids', 'advance_ids.amount_total')
    def _compute_total_advances(self):
        """
            computes advance amount total related to the invoice.
        """
        for inv in self:
            inv.total_advances = sum(inv.advance_ids.mapped('amount_total'))

    def action_post(self):
        """
            Inheritance to refund advance invoices if current invoice was made
            with all sale order amount without deduct advances
        """
        if not self.is_final and not self.l10n_mx_edi_origin and self.relate_advances:
            raise UserError(
                _("If you mark the field 'relate invoices' you have to add invoices "
                    "in the page 'related invoices' and relate them to this invoice."))
        if self.is_final and not self.final_no_advances and self.relate_advances and self.advance_ids:
            # if the invoice has to deduct advances we have to add each advance amount as an item on
            # line_ids.
            line_ids = self.line_ids
            # debit lines
            line_ids += self.invoice_line_move_total_advance()
            # credit lines
            line_ids += self.invoice_line_move_line_advances()
            self.write({'line_ids': line_ids})
        res = super(AccountMove, self).action_post()
        # if the invoice which is being posted is an out_refund invoice
        # we add the refund to the out invoice as a payment.
        if self.is_refund and self.reversed_entry_id.id:
            partner_account = self.partner_id.property_account_receivable_id.id
            if partner_account:
                credit_aml_id = self.line_ids.filtered(lambda rec: rec.account_id.id == partner_account)
                if credit_aml_id:
                    self.reversed_entry_id.js_assign_outstanding_line(credit_aml_id[0].id)
        # if the invoice which is being posted isn't deducting the advances, we have to create
        # the refund invoice in order to return the advances related to the invoice.
        if self.is_final and self.final_no_advances and self.advance_ids and self.relate_advances:
            self.return_advance()
        return res

    def return_advance(self):
        """
            Create a refund invoice taken as base an advance invoice
        """
        refund_ids = self.env['account.move']
        advance_line_vals = []
        for inv in self:
            total_advances = 0.0
            advance_values = {
                'invoice_date': inv.invoice_date,
                'invoice_origin': inv.name,
                'reversed_entry_id': inv.id,
                'move_type': 'out_refund',
                'state': 'draft',
                'is_refund': True,
                'relate_advances': True,
                'invoice_date_due': inv.invoice_date_due,
                'partner_id': inv.partner_id.id,
                'currency_id': inv.currency_id.id,
                'journal_id': inv.journal_id.id,
                'fiscal_position_id': inv.fiscal_position_id.id,
                'l10n_mx_edi_origin': '07|',
            }
            product_id = self.get_default_product_id()
            account_id = product_id.property_account_income_id.id or product_id.\
                categ_id.property_account_income_categ_id.id
            refund_id = self.env['account.move'].create(advance_values)
            refund_ids |= refund_id
            taxes = refund_id.fiscal_position_id.map_tax(product_id.taxes_id).ids
            total_advances = sum(inv.advance_ids.mapped('amount_total'))
            invoice_line_values = {
                'product_id': product_id.id,
                'move_id': refund_id.id,
                'account_id': account_id,
                'quantity': 1,
                'name': product_id.name,
                'product_uom_id': product_id.uom_id.id,
                'price_unit': total_advances,
                'tax_ids': [(6, 0, taxes)] or [],
            }
            self.env['account.move.line'].with_context(check_move_validity=False).create(invoice_line_values)
            refund_id.with_context(check_move_validity=False)._recompute_dynamic_lines(recompute_all_taxes=True)
            refund_id._recompute_tax_lines()
            if refund_id.name == '/':
                refund_name = _('Rectificative')
            else:
                refund_name = refund_id.name
            refund_msg = _('This rectificative has been create from:') + " <a href=# data-oe-model=account.move data-oe-id=%d>%s</a>" % (inv.id, inv.name)
            move_msg = _('A rectificave has been created from this invoice:') + " <a href=# data-oe-model=account.move data-oe-id=%d>%s</a>" % (refund_id.id, refund_name)
            inv.message_post(body=move_msg)
            refund_id.message_post(body=refund_msg)
            advance_line_vals.append(self.prepare_advance_values(refund_id.id, inv.id))
            advance_line_vals.append(self.prepare_advance_values(inv.id, refund_id.id))
            self.env['cfdi.advances'].create(advance_line_vals)
        return refund_ids

    @api.model
    def prepare_advance_values(self, invoice_id, advance_id):
        return {
            'sequence': 10,
            'advance_id': advance_id,
            'invoice_id': invoice_id,
        }

