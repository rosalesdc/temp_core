#########################################################
# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2023 Birtum - https://www.birtum.com
# All Rights Reserved.
#
# Developer(s): Eddy Luis Pérez Vila <epv@birtum.com>
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
##########################################################
import base64
import logging
import time

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .portal_sat import PortalSAT

TRY_COUNT = 3


_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends("currency_id", "company_id.currency_id")
    def _compute_not_company_currency(self):
        self.not_company_currency = (
            self.currency_id and self.currency_id != self.company_id.currency_id
        )

    not_company_currency = fields.Boolean(
        "Use Custom Currency Rate", compute="_compute_not_company_currency"
    )

    sat_document_id = fields.Many2one(
        "sat.documents", string="CFDI", readonly=True)

    use_custom_rate = fields.Boolean(
        "Use Custom Rate",
        readonly=True,
        default=False,
        states={"draft": [("readonly", False)]},
    )

    custom_rate = fields.Float(
        string="Custom Rate",
        digits=(12, 6),
        store=True,
        readonly=False,
        compute="_compute_custom_rate",
    )

    currency_rate = fields.Float(
        string="System Currency Rate",
        compute="_compute_currency_rate",
        digits=(12, 6),
        readonly=True,
        help="Currency rate of this invoice",
    )
    
    l10n_mx_edi_cfdi_uuid_in_invoice = fields.Char(
        string="Folio Fiscal",
    )

    def _inverse_amount_total(self):
        """
            inherited method in order to compute the amount total in company currency
            using custom rate.
        """
        for move in self:
            super(AccountMove, move.with_context(
                use_custom_rate=move.use_custom_rate,
                custom_rate=move.custom_rate))._inverse_amount_total()
            
    @api.depends(
        "currency_id", "not_company_currency", "use_custom_rate", "invoice_date"
    )
    def _compute_currency_rate(self):
        self.env["account.move"].flush_recordset(["not_company_currency"])
        for invoice in self:
            if not invoice.is_invoice(include_receipts=True):
                invoice.currency_rate = 0
                continue
            if invoice.currency_id and invoice.not_company_currency:
                rate = invoice.getting_currency_rate(
                    invoice.currency_id, invoice.invoice_date, invoice.company_id
                )
                invoice.currency_rate = rate
            else:
                invoice.currency_rate = 1

    @api.model
    def getting_currency_rate(self, currency_id, date_order, company_id):
        currency_rates = currency_id._get_rates(
            company_id, (date_order or fields.Date.today())
        )
        return (
            1 / (currency_rates.get(currency_id.id) or currency_id.rate)
            if currency_rates
            else 1
        )

    @api.depends(
        "use_custom_rate", "move_type", "not_company_currency", "currency_rate"
    )
    def _compute_custom_rate(self):
        for move in self:
            if move.not_company_currency and not move.use_custom_rate:
                move.custom_rate = move.currency_rate
            elif move.not_company_currency and move.use_custom_rate:
                move.custom_rate = move.custom_rate
            else:
                move.custom_rate = move.currency_rate

    @api.constrains("sat_document_id")
    def _link_sat_document(self):
        for move in self:
            move.sat_document_id.move_id = move.id

    def action_view_sat_document(self):
        self.ensure_one()
        result = self.env["ir.actions.actions"]._for_xml_id(
            "l10n_mx_sat_sync.entry_sat_documents_action"
        )
        if len(self.sat_document_id) > 1:
            result["domain"] = [("id", "in", self.sat_document_id.ids)]
        elif len(self.sat_document_id) == 1:
            res = self.env.ref(
                "l10n_mx_sat_sync.sat_documents_view_form", False)
            form_view = [(res and res.id or False, "form")]
            if "views" in result:
                result["views"] = form_view + [
                    (state, view) for state, view in result["views"] if view != "form"
                ]
            else:
                result["views"] = form_view
            result["res_id"] = self.sat_document_id.id
        else:
            result = {"type": "ir.actions.act_window_close"}
        return result

    def action_move_cancellation_downgload(self):
        l10n_mx_edi_cfdi_uuid = self.l10n_mx_edi_cfdi_uuid
        if self.l10n_mx_edi_sat_status != "cancelled":
            raise UserError(_("This document has not be canceled."))
        if not l10n_mx_edi_cfdi_uuid and self.l10n_mx_edi_origin:
            l10n_mx_edi_cfdi_uuid = self.l10n_mx_edi_origin.split("|")[1]
        if not l10n_mx_edi_cfdi_uuid:
            cfdi_data = base64.decodebytes(self.attachment_ids.search([('name', 'like', '%-MX-Invoice-4.0.xml'), (
                'res_model', '=', 'account.move'), ('res_id', '=', self.id)], limit=1, order='create_date desc').with_context(bin_size=False).datas)
            cfdi_infos = self._l10n_mx_edi_decode_cfdi(cfdi_data)
            l10n_mx_edi_cfdi_uuid = cfdi_infos.get('uuid')
        if l10n_mx_edi_cfdi_uuid:
            end_date = fields.Datetime.context_timestamp(
                self, fields.Datetime.now())
            if self.company_id.last_cfdi_fetch_date:
                start_date = fields.Datetime.context_timestamp(
                    self, self.company_id.last_cfdi_fetch_date
                )
            else:
                now_date = fields.Datetime.now().replace(hour=0, minute=0)
                start_date = fields.Datetime.context_timestamp(self, now_date)

            esignature = self.company_id.l10n_mx_edi_esign_ids.with_user(
                self.env.user
            )._get_valid_certificate()
            if not esignature:
                raise UserError(_("Files uploaded are not FIEL files."))
            if not esignature.content or not esignature.key or not esignature.password:
                raise UserError(
                    _("Select the correct FIEL files (.cer or .pem)."))
            # Diccionario para request al SAT
            opt = {
                "credenciales": None,
                "rfc": None,
                "uuid": l10n_mx_edi_cfdi_uuid,
                "ano": None,
                "mes": None,
                "dia": 0,
                "intervalo_dias": None,
                "fecha_inicial": None,
                "fecha_final": None,
                "tipo": "t",
                "tipo_complemento": "-1",
                "rfc_emisor": None,
                "rfc_receptor": None,
                "sin_descargar": False,
                "base_datos": False,
                "directorio_fiel": "",
                "archivo_uuids": "",
                "estatus": False,
            }
            if start_date and end_date:
                opt["fecha_inicial"] = start_date
                opt["fecha_final"] = end_date

            # Conexión al SAT y request para obtener documentos
            fiel_cert_data = base64.b64decode(esignature.content)
            fiel_pem_data = esignature._get_pem_key(
                esignature.key, esignature.password)
            sat = None
            for i in range(TRY_COUNT):
                sat = PortalSAT(opt["rfc"], "cfdi-descarga", False)
                if sat.login_fiel(fiel_cert_data, fiel_pem_data):
                    time.sleep(1)
                    break
            supplier_invoices_data, issued_invoices_data = {}, {}
            if sat and sat.is_connect:
                supplier_invoices_data, issued_invoices_data = sat.search(opt)
                sat.logout()
            elif sat:
                sat.logout()

            # Procesamiento de documentos obtenidos del SAT
            if not supplier_invoices_data and not issued_invoices_data:
                return
            sat_docs = (supplier_invoices_data, issued_invoices_data)
            for sat_doc in sat_docs:
                _logger.info("Processing %s CFDI documents." %
                             len(sat_doc.items()))
                for uuid, data in sat_doc.items():
                    if data[2]:
                        pdf_content = data[2]
                        pdf_node = base64.b64encode(pdf_content)

                        attachment = self.env["ir.attachment"].create(
                            {
                                "name": "Acuse de cancelación de CFDI.pdf",
                                "res_id": self.id,
                                "res_model": self._name,
                                "datas": pdf_node,
                                "type": "binary",
                                "mimetype": "application/pdf",
                            }
                        )
                        if attachment:
                            self.message_post(attachment_ids=attachment.ids)
                    if data[3]:
                        pdf_content = data[3]
                        pdf_node = base64.b64encode(pdf_content)

                        attachment = self.env["ir.attachment"].create(
                            {
                                "name": "Acuse de solicitud de Cancelación de CFDI.pdf",
                                "res_id": self.id,
                                "res_model": self._name,
                                "datas": pdf_node,
                                "type": "binary",
                                "mimetype": "application/pdf",
                            }
                        )
                        if attachment:
                            self.message_post(attachment_ids=attachment.ids)
                    if not data[2] and not data[3]:
                        raise UserError(
                            _("This document has not be canceled."))


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    use_custom_rate = fields.Boolean(
        related="move_id.use_custom_rate",
        string="Use Custom Rate",
        readonly=True,
        copy=False,
    )
    custom_rate = fields.Float(
        related="move_id.custom_rate",
        string="Custom Rate",
        digits=(12, 6),
        copy=False,
        readonly=True,
    )


    @api.depends('currency_id', 'company_id', 'move_id.date', 'use_custom_rate', 'custom_rate')
    def _compute_currency_rate(self):
        """
            tool method to compute the currency rate of the system at invoice
            date.
        """
        for line in self:
            if line.use_custom_rate and line.custom_rate:
                super(AccountMoveLine, line.with_context(
                    use_custom_rate=line.use_custom_rate,
                    custom_rate=line.custom_rate))._compute_currency_rate()
            else:
                super(AccountMoveLine, line)._compute_currency_rate()
                
    @api.onchange("amount_currency")
    def _onchange_amount_currency(self):
        for line in self:
            if not line.move_id.is_invoice(include_receipts=True):
                continue
            company = line.move_id.company_id
            if self.custom_rate and self.use_custom_rate:
                balance = line.currency_id.with_context(
                    use_custom_rate=True, custom_rate=self.custom_rate
                )._convert(
                    line.amount_currency,
                    company.currency_id,
                    company,
                    line.move_id.date,
                )
            else:
                balance = line.currency_id._convert(
                    line.amount_currency,
                    company.currency_id,
                    company,
                    line.move_id.date,
                )
            line.debit = balance if balance > 0.0 else 0.0
            line.credit = -balance if balance < 0.0 else 0.0

            line.update(line._get_fields_onchange_subtotal_model())

    @api.onchange(
        "quantity",
        "discount",
        "price_unit",
        "tax_ids",
        "price_total",
        "use_custom_rate",
        "custom_rate",
    )
    def _onchange_price_subtotal(self):
        for line in self:
            if not line.move_id.is_invoice(include_receipts=True):
                continue
            line.update(line._get_fields_onchange_subtotal_model())

    @api.model
    def _get_fields_onchange_subtotal_model(self):
        if self.move_id.move_type in self.move_id.get_outbound_types(include_receipts=True):
            sign = 1
        elif self.move_id.move_type in self.move_id.get_inbound_types(include_receipts=True):
            sign = -1
        else:
            sign = 1
        price_subtotal = self.price_subtotal*sign
        if self.currency_id and self.currency_id != self.move_id.company_id.currency_id:
            if self.custom_rate and self.use_custom_rate:
                # Multi-currencies.
                balance = self.currency_id.with_context(
                    use_custom_rate=self.use_custom_rate,
                    custom_rate=self.custom_rate,
                )._convert(price_subtotal, self.move_id.company_id.currency_id, self.move_id.company_id, self.invoice_date or self.date)
                return {
                    "amount_currency": price_subtotal,
                    "debit": balance > 0.0 and balance or 0.0,
                    "credit": balance < 0.0 and -balance or 0.0,
                }
        else:
            return {}
        return {}


class ResCurrency(models.Model):
    _inherit = "res.currency"

    @api.model
    def _get_conversion_rate(self, from_currency, to_currency, company, date):
        use_custom_rate = self._context.get("use_custom_rate")
        custom_rate = self._context.get("custom_rate")
        if use_custom_rate and custom_rate:
            return (1/custom_rate)
        else:
            return super()._get_conversion_rate(
                from_currency, to_currency, company, date
            )
