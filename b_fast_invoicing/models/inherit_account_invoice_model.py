# -*- encoding: utf-8 -*-
#
# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2023 Birtum - http://www.birtum.com/
# All Rights Reserved.
#
# Developer(s): Eddy Luis Pérez Vila
#               (epv@birtum.com)
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
from datetime import datetime, timedelta

import json
from psycopg2 import OperationalError, errorcodes

from odoo import SUPERUSER_ID, _, api, fields, models
#from odoo.addons.l10n_mx_edi.tools.run_after_commit import run_after_commit
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):
    _inherit = 'account.move'

    auto_payment_policy = fields.Char(
        size=3
    )
    auto_invoice_vat = fields.Char()
    auto_invoice_partner = fields.Char()
    from_auto_invoice = fields.Boolean()

    def _l10n_mx_edi_get_payment_policy(self):
        self.ensure_one()
        if self.auto_payment_policy:
            return self.auto_payment_policy
        return super(AccountInvoice, self)._l10n_mx_edi_get_payment_policy()

    def get_xml_file_url(self):
        self.ensure_one()
        #version = self.l10n_mx_edi_get_pac_version()
        # filename = ('%s-%s-MX-Invoice-%s.xml' % (
        #     self.journal_id.code, self.name, version.replace('.', '-'))).replace('/', '')
        filename = ('%s-%s-MX-Invoice.xml' % (
            self.journal_id.code, self.name))
        attachment = self.env['ir.attachment'].with_user(SUPERUSER_ID).search([
            ('name', '=', filename),
            ('res_id', '=', self.id),
            ('res_model', '=', 'account.move')
        ], limit=1)
        if not attachment:
            return False
        # ATTACHMENT MUST BE PUBLIC
        attachment.write({'public': True})
        xml_url = '/web/content/{}?download=true'.format(attachment.id)
        if attachment.access_token:
            xml_url += '&access_token={}'.format(attachment.access_token)
        return xml_url

    @api.model
    def cron_call_order_invoice_process(self):
        """
        TODO:
        :return: True
        """
        if not self.env.user.company_id.fi_generic_vat_number:
            raise UserError(_('There is no a generic vat number defined for massive invoicing!'))
        sale_obj = self.env['sale.order']
        sale_obj.cron_invoice_all()
        return True

    @api.model
    def cron_call_order_re_invoice_process(self, limit=None):
        """
        TODO:
        :return: True
        """
        last_day = (fields.Date.today() + timedelta(days=1)).day == 1
        if not last_day:
            return False
        last = fields.Datetime.now()
        first = datetime(day=1, month=last.month, year=last.year, minute=0, hour=0, second=0)
        if not self.env.user.company_id.fi_generic_vat_number:
            raise UserError(_('There is no a generic vat number defined for massive invoicing!'))
        sale_obj = self.env['sale.order']
        sale_obj.cron_re_invoice_all(first, last, limit=limit)
        return True

    def fast_invoicing_auto_pay(self):
        self.ensure_one()
        if  not self.l10n_mx_edi_cfdi_uuid:
            return False
        if self.env.context.get('fast_invoicing_apply_payment', False):
            so_ids = self.mapped('invoice_line_ids.sale_line_ids.order_id').ids
            # MAKING PAYMENTS
            if self.invoice_has_outstanding:
                outstanding_credits_debits = json.loads(
                    self.invoice_outstanding_credits_debits_widget)
                lines = sorted(outstanding_credits_debits['content'],
                               key=lambda ml: ml['amount'], reverse=True)
                for line in lines:
                    payment = self.env['account.move.line'].browse(line['id']).payment_id
                    if payment.reserved_order_id and payment.reserved_order_id.id not in so_ids:
                        continue
                    try:
                        self.with_context(
                            default_type='entry').js_assign_outstanding_line(line['id'])
                        if self.payment_state == 'paid':
                            break
                    except Exception as e:
                        self.message_post(body=str(e))
                        raise UserError(str(e))
        return True

    def js_assign_outstanding_line(self, line_id):
        line = self.env['account.move.line'].browse(line_id)
        sale_order_ids = self.mapped('invoice_line_ids.sale_line_ids.order_id').ids
        payment = line.payment_id
        if payment.reserved_order_id and payment.reserved_order_id.id not in sale_order_ids:
            raise UserError(
                _('This payment is reserved for SO %s') % payment.reserved_order_id.name)
        return super().js_assign_outstanding_line(line_id)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def get_amount_to_show(self, move):
        self.ensure_one()
        if self.currency_id and self.currency_id == move.currency_id:
            amount_to_show = abs(self.amount_residual_currency)
        else:
            currency = self.company_id.currency_id
            amount_to_show = currency._convert(
                abs(self.amount_residual), move.currency_id, move.company_id,
                self.date or fields.Date.today())
        return amount_to_show


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    @api.model
    def cron_invoice_all(self):
        orders = self.search([
            ('invoice_status', '=', 'to invoice')])
        if not orders:
            return False
        ctx = dict(
            allow_use_generic_vat=self.env.user.company_id.fi_generic_vat_number,
            allow_use_generic_partner=self.env.user.company_id.fi_res_partner
        )
        moves = self.env['account.move']
        for order in orders:
            try:
                moves |= order.with_context(**ctx)._create_invoices()
            except UserError as error:
                _logger.info(error.name)
                continue
        moves = moves.sorted('move_type').filtered(lambda x: x.state not in ('cancel'))
        batches = [moves[index:index + 50] for index in range(0, len(moves), 50)]
        for invoices in batches:
            try:
                for invoice in invoices:
                    try:
                        # Cambiamos la fecha por la actual
                        invoice.invoice_date = fields.Date.today()
                        # CONFIRM INVOICE
                        confirm_context = dict(
                            with_company=self.env.user.company_id.id,
                            disable_after_commit=True
                        )
                        #invoice.with_context(**confirm_context)._post()
                        invoice.with_context(
                            fast_invoicing_apply_payment=True).fast_invoicing_auto_pay()
                        self.env.cr.commit()

                        # Añadiendo logica para el metodo de pago
                        if invoice.move_type == 'out_invoice':
                            payment_obj = self.env['account.payment']
                            payments = payment_obj.with_user(SUPERUSER_ID).search([
                                ('partner_id', '=', invoice.partner_id.id),
                                ('payment_type', '=', 'inbound'),
                                ('partner_type', '=', 'customer'),
                                ('state', '=', 'posted')
                            ])
                            if payments:
                                move_lines = payments.mapped('move_line_ids').filtered(
                                    lambda ml: not ml.reconciled and ml.credit > 0.0).sorted(
                                    lambda ml: ml.get_amount_to_show(invoice), reverse=True)
                                if move_lines:
                                    payment_method = move_lines[:1].payment_id.l10n_mx_edi_payment_method_id.id
                                if payment_method:
                                    invoice.l10n_mx_edi_payment_method_id = payment_method

                    except Exception as e:
                        _logger.info(str(e))
                        self.env.cr.rollback()
                        continue
            except OperationalError:
                _logger.error('A batch of moves could not be published :%s', repr(invoices))
                continue
        return True