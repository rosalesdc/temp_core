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
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import base64


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_substitution_invoice = fields.Boolean(
        string='Is substituted invoice',
        readonly=True,
        default=False,
        copy=False,
        help='Helps us to identify if the invoice has been created from another invoice '
             'using the button CREATE SUBSTITUTED INVOICE'
    )
    origin_invoice_id = fields.Many2one(
        'account.move',
        string='Origin invoice',
        default=False,
        readonly=True,
        help='The origin invoice from the substitued invoice was created, it takes a value '
             'when the substituted invoice is created using the button.'
    )
    reversal_invoice_id = fields.Many2one(
        'account.move',
        string='Reversal invoice',
        copy=False,
        default=False,
        help='This the reversal invoice created from the current invoice, represents a balanced cancellation.'
    )

    ################################################################################
    #                               TOOL METHODS
    ################################################################################

    def action_reverse(self):
        """
            - inherited method in order to avoid to create a credit note if the invoice
              is fully paid.
            - In v14 invoice_payment_state does not exists.
        """
        if self.payment_state in ['paid','reversed'] and self.move_type == 'out_invoice' and self.reversal_invoice_id:
            raise ValidationError(
                _('It is not possible create a credit note, due to the current invoice has been '
                  'fully paid.'))
        return super(AccountMove, self).action_reverse()

    def create_substituted_invoice(self):
        """
            - lauches the action view to create a substituted invoice of the 
              current invoice.
        """
        return self.env.ref('b_advanced_invoice_cancel.action_view_account_move_reversal').read()[0]

    @api.model
    def _create_reversal_invoice(self, source_invoice):
        """
            - tool method to create a reversal invoice.
            :receive: source_invoice: The invoice from a reversal will be created.
        """
        vals = self._prepare_default_reversal_invoice(source_invoice)
        reversal_vals = source_invoice._reverse_move_vals(vals, True)
        reverse_id = self.env['account.move'].create(reversal_vals)
        reverse_id.with_context(move_reverse_cancel=True)._post()
        accounts = source_invoice.mapped('line_ids.account_id') \
            .filtered(lambda account: account.reconcile or account.internal_type == 'liquidity')
        for account in accounts:
            (source_invoice.line_ids + reverse_id.line_ids)\
                .filtered(lambda line: line.account_id == account and line.balance)\
                .reconcile()
        
        source_invoice.reversal_invoice_id = reverse_id
        return True

    @api.model
    def _prepare_default_reversal_invoice(self, move):
        return {
            'ref': _('Reversal of: %s') % (move.name),
            'date': fields.Date.context_today(self),
            'invoice_date': fields.Date.context_today(self),
            'journal_id': move.journal_id.id,
            'move_type': 'entry',
            'reversed_entry_id': move.id,
            'invoice_payment_term_id': None,
            'invoice_user_id': move.invoice_user_id.id,
        }

    def is_edi_mx_cancelled(self):
        for document in self.edi_document_ids:
            if document.state == 'cancelled' and document.edi_format_id.code == 'cfdi_3_3':
                return True

    def button_cancel(self):
        """
            - inherited method in order to validate if the invoice has been cancelled by SAT
              and it has a reversal invoice, if it is, we have to avoid to set the invoice state
              to cancel, because the invoice is accounting cancelled with the reversal.
        """
        if self.posted_before and not self.reversal_invoice_id:
            self.write({'state': 'posted'})
            self._create_reversal_invoice(self)
            
        #Maintain posted status
        if self.is_edi_mx_cancelled() and self.l10n_mx_edi_sat_status == 'cancelled' and self.reversal_invoice_id:
            self.write({'auto_post': False, 'state': 'posted'})
        else:
            return super(AccountMove, self).button_cancel()
        

    def button_draft(self):
        """
            - inherited method in order to avoid the invoice set to draft, if it has
              reversal entry related to it.
        """
        #The following commented line is only to force the field value for testing, has to be removed in prodution.
        #self.write({'l10n_mx_edi_sat_status': 'cancelled'})
        if self.reversal_invoice_id:
            raise ValidationError(
                _('It is not possible to set the invoice to draft, due to it has been reconciled '
                  'with a reverse entry.'))
        return super(AccountMove, self).button_draft()

    def _post(self, soft=True):
        """
            - Inherited method in order give a value to the field posted_before.
              this fields helps us to identify if the invoice has been previously
              posted.
        """
        res = super()._post(soft=soft)
        self.write({'posted_before': True})
        return res

    def _compute_amount(self):
        """
        Inherited method to force payment status field in Reversed if conditions are met
        """
        super(AccountMove, self)._compute_amount()
        for record in self:
            if record.is_edi_mx_cancelled() and record.l10n_mx_edi_sat_status == 'cancelled' and record.reversal_invoice_id:
                record.payment_state = 'reversed'
    

    def _compute_cfdi_values(self):
        """Inherited method to put the Folio Fiscal even if the document is unlinked.
        """
        super(AccountMove, self)._compute_cfdi_values()
        for move in self:
            if move.is_edi_mx_cancelled() and move.l10n_mx_edi_sat_status == 'cancelled' and move.reversal_invoice_id:
                cfdi_doc = move.edi_document_ids.filtered(lambda document: document.edi_format_id == self.env.ref('l10n_mx_edi.edi_cfdi_3_3'))
                if cfdi_doc and not cfdi_doc.attachment_id:
                    attachment = self.env['ir.attachment'].search([('name', 'like', '%-MX-Invoice-4.0.xml'), ('res_model', '=', 'account.move'), ('res_id', '=', move.id)], limit=1, order='create_date desc')
                    if attachment:
                        cfdi_data = base64.decodebytes(attachment.with_context(bin_size=False).datas)
                        cfdi_infos = move._l10n_mx_edi_decode_cfdi(cfdi_data=cfdi_data)
                        self.l10n_mx_edi_cfdi_uuid = cfdi_infos['uuid']
                                
    #WHEN THE CRON IS CALLED AND THE SAT STATUS IS CANCELLED, do not put the cancelled invoice, just make your policy reverse, 
    #how to test this in a test environment?
    def l10n_mx_edi_update_sat_status(self):
        """
            - inherited method in order to create a reversal invoice of the current invoice
              if it is cancelled by SAT.
            - if the invoice has payments, they have to be removed in order to be
              consistent with the processs.
            - The invoice is conciled with the reversal invoice.
        """
        res = super(AccountMove, self).l10n_mx_edi_update_sat_status()
        # TODO
        # every time this method is called, we set up the field l10n_mx_edi_sat_status
        # to cancelled, for testing purposes.This line has to be removed in prodution.
        #self.write({'l10n_mx_edi_sat_status': 'cancelled'})
        #TODO 
        cfdi_doc = self.edi_document_ids.filtered(lambda document: document.edi_format_id == self.env.ref('l10n_mx_edi.edi_cfdi_3_3'))
        if cfdi_doc:
            cfdi_doc.state='cancelled'

        for record in self:
            if not record.reversal_invoice_id:
                record.mapped('line_ids').remove_move_reconcile()
                record._create_reversal_invoice(record)
                record.write({'state': 'posted'})
                return res
        return res