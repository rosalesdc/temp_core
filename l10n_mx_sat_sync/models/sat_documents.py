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

from lxml import etree
from lxml.objectify import fromstring
from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'
    
    def _get_move_applicability(self, move):
        if move.sat_document_id:
            return False
        else:
            return super(AccountEdiFormat, self)._get_move_applicability(move)


class SatDocuments(models.Model):
    _name = "sat.documents"
    _description = "SAT documents"
    _order = "date desc"

    name = fields.Char(string="UUID", required=True, copy=False)
    number = fields.Char("Number")
    series = fields.Char("Series")
    date = fields.Datetime("Date", required=True)
    stamp_date = fields.Datetime("Issuing date", required=True)
    currency_id = fields.Many2one("res.currency", string="Currency", required=True)
    currency_rate = fields.Float("Rate", digits=(12, 6))
    amount = fields.Monetary("Amount", required=True)
    issuing_partner = fields.Char("Issuing partner", required=True)
    issuing_partner_vat = fields.Char("Issuing partner VAT", required=True)
    receiver_partner = fields.Char("Receiver partner", required=True)
    receiver_partner_vat = fields.Char("Receiver partner VAT", required=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    cfdi_type = fields.Selection(
        [
            ("I", "I - Entry"),
            ("E", "E - Issued"),
            ("P", "P - Payments"),
            ("N", "N - Payroll"),
            ("T", "T - Pickings"),
        ],
        "Document type",
        required=True,
    )
    issuing_type = fields.Selection(
        [("I", "Issued"), ("R", "Received")], "Issuing type"
    )
    cfdi_version = fields.Selection([("3.3", "3.3"), ("4.0", "4.0")], "Version")
    payment_method = fields.Char(string="Payment method")
    payment_way_id = fields.Many2one(
        "l10n_mx_edi.payment.method",
        string="Payment Way",
        help="Indicates the way the invoice was/will be paid, where the options could be: "
        "Cash, Nominal Check, Credit Card, etc. Leave empty if unkown and the XML will show 'Unidentified'.",
    )
    notes = fields.Text(
        "Notes",
        help="Enter here the internal notes for this document (ex: Offer sent to supplier).",
    )
    xml_attachment = fields.Binary(string="XML attachment", required=True, copy=False)
    xml_filename = fields.Char(string="XML filename", required=True, copy=False)
    move_id = fields.Many2one("account.move", string="Move", readonly=True)

    _sql_constraints = [("unique_name", "UNIQUE(name)", "Cannot duplicate CFDI UUID.")]

    def unlink(self):
        for doc in self:
            if doc.move_id:
                raise UserError(
                    _(
                        "Cannot delete the document %s because has the move ID %s related.",
                        doc.name,
                        doc.move_id.id,
                    )
                )
        return super().unlink()

    def create_invoice(self):
        context = self._context
        docs = (
            self.env[context.get("active_model")].browse(context.get("active_ids", [0]))
            if context.get("active_ids", False)
            else self
        )
        # Búsqueda de los partners seleccionados
        partner_ids = self.env["res.partner"].search(
            []
        )
        # Búsqueda de taxes de compras
        tax_ids = self.env["account.tax"].search(
            [
                ("amount_type", "in", ["fixed", "percent"]),
            ]
        )
        uom_ids = self.env["uom.uom"].search([])

        def _doc_validations(doc):
            if doc.move_id:
                return None, _(
                    "\n- %s: This invoice has been already created.", doc.name
                )
            return doc, None

        def _partner_validations(partner_ids, doc):
            partner = partner_ids.filtered(lambda p: p.vat == doc.issuing_partner_vat)
            if self.issuing_type == 'I':
                partner = partner_ids.filtered(lambda p: p.vat == doc.receiver_partner_vat)
            if len(partner) > 1:
                part = partner[0]
                partner = partner.filtered(lambda p: p.name == doc.issuing_partner)
                if self.issuing_type == 'I':
                    partner = partner.filtered(lambda p: p.name == doc.receiver_partner)
                if not partner:
                    partner = part
                if len(partner) > 1:
                    if self.issuing_type != 'I':
                        return None, _(
                            "\n- %s: There are multiple records for partner %s - %s.",
                            doc.name,
                            doc.issuing_partner,
                            doc.issuing_partner_vat,
                        )
                    else:
                        return None, _(
                            "\n- %s: There are multiple records for partner %s - %s.",
                            doc.name,
                            doc.receiver_partner,
                            doc.receiver_partner_vat,
                        )
                        
            if not partner:
                if self.env.company.load_data_master_from_xml:
                    country_id_aux = self.env['res.country'].search([('code', '=', 'MX')], limit=1)
                    
                    if self.issuing_type != 'I':
                        partner = self.env['res.partner'].create({
                            'country_id': country_id_aux.id,
                            'name': doc.issuing_partner,
                            'vat': doc.issuing_partner_vat
                        })
                    else:
                        partner = self.env['res.partner'].create({
                            'country_id': country_id_aux.id,
                            'name': doc.receiver_partner,
                            'vat': doc.receiver_partner_vat
                        })
                        
                else:
                    
                    if self.issuing_type != 'I':
                        return None, _(
                            "\n- %s: There are not records for partner %s - %s.",
                            doc.name,
                            doc.issuing_partner,
                            doc.issuing_partner_vat,
                        )
                    else:
                        return None, _(
                            "\n- %s: There are not records for partner %s - %s.",
                            doc.name,
                            doc.receiver_partner,
                            doc.receiver_partner_vat,
                        )
            return partner, None

        def read_cfdi_data(doc):
            cfdi_data = base64.decodebytes(doc.xml_attachment)
            try:
                cfdi_node = fromstring(cfdi_data)
            except etree.XMLSyntaxError as e:
                return None, _("Cannot open CFDI data (%s) beacuse: %s", doc.name, e)
            except AttributeError as e:
                return None, _("Cannot open CFDI data (%s) beacuse: %s", doc.name, e)
            return cfdi_node, None

        def get_cfdi_lines(doc, cfdi, tax_ids, uom_ids):
            lines = []
            try:
                concepts = cfdi.Conceptos
            except etree.XMLSyntaxError as e:
                return None, _("Cannot open CFDI lines (%s) beacuse: %s", doc.name, e)
            except AttributeError as e:
                return None, _("Cannot open CFDI lines (%s) beacuse: %s", doc.name, e)
            for concept in concepts.iterchildren():
                price_unit = float(concept.get("ValorUnitario", 0))
                quantity = float(concept.get("Cantidad", 1))
                if concept.get("Descuento", False):
                    amount_total = float(concept.get("Importe"))
                    discount = float(concept.get("Descuento"))
                    price_unit = (amount_total - discount) / quantity
                vals = {
                    "name": concept.get("Descripcion", ""),
                    "quantity": quantity,
                    "price_unit": price_unit,
                }
                matched_uom = uom_ids.filtered(
                    lambda u: u.unspsc_code_id.code == concept.get("ClaveUnidad")
                )
                if matched_uom:
                    vals["product_uom_id"] = matched_uom[0].id
                    matched_uom = matched_uom[0]
                if list(concept.iterchildren()):
                    try:
                        tax_types = concept.Impuestos
                    except etree.XMLSyntaxError as e:
                        return None, _(
                            "Cannot open CFDI taxes lines (%s) beacuse: %s", doc.name, e
                        )
                    except AttributeError as e:
                        return None, _(
                            "Cannot open CFDI taxes lines (%s) beacuse: %s", doc.name, e
                        )
                    taxes = []
                    for tax_type in tax_types.iterchildren():
                        for tax in tax_type.iterchildren():
                            factor_type = tax.get("TipoFactor")
                            tax_code = tax.get("Impuesto")
                            amount = (
                                float(tax.get("TasaOCuota", 0)) * 100
                                if "Traslado" in tax.tag
                                else float(tax.get("TasaOCuota", 0)) * -100
                            )
                            type_imp = "sale" if self.issuing_type == 'I' else 'purchase'
                            if type_imp == 'purchase':
                                amount = amount * -1
                            matched_tax = tax_ids.filtered(
                                lambda t: t.l10n_mx_tax_type == factor_type
                                and t.l10n_mx_tax_code == tax_code
                                and t.type_tax_use == type_imp
                                and t.amount == amount
                            )
                            if matched_tax:
                                taxes.append(matched_tax[0].id)
                            else:
                                if self.env.company.load_data_master_from_xml:
                                    tx_created = self.env['account.tax'].create({
                                        'name': 'tx_created_' + tax_code,
                                        'l10n_mx_tax_type': factor_type,
                                        'l10n_mx_tax_code': tax_code,
                                        'type_tax_use': type_imp,
                                        'amount': amount
                                    })
                                    taxes.append(tx_created.id)
                                else:
                                    return None, _(
                                        "\n- %s: Cannot match an appropiate tax to concept %s",
                                        doc.name,
                                        vals["name"],
                                    )
                    vals["tax_ids"] = [(6, 0, taxes)]
                unspsc_code = concept.get("ClaveProdServ")
                product_id = self.env["product.product"].search(
                    [("unspsc_code_id.code", "=", unspsc_code)], limit=1
                )
                if not product_id:
                    if self.env.company.load_data_master_from_xml:
                        unspsc_code =  self.env['product.unspsc.code'].search([('code', '=', unspsc_code)],
                                                                              limit=1)
                        product_id = self.env['product.product'].create({
                            'name': concept.get('Descripcion'),
                            'lst_price': concept.get('Importe'),
                            'uom_id': matched_uom.id,
                            'uom_po_id': matched_uom.id,
                            'unspsc_code_id': unspsc_code and unspsc_code.id
                        })
                    else: 
                        return None, _(
                            "\n- %s: Cannot match an appropiate product to concept [%s] %s",
                            doc.name,
                            unspsc_code,
                            vals["name"],
                        )
                vals["product_id"] = product_id.id
                lines.append(vals)
            return lines, None

        move_vals = []
        doc_errors = ""
        partner_errors = ""
        attachment_errors = ""
        line_errors = ""
        total_errors = 0
        AccountMove = self.env["account.move"]
        for doc in docs:
            doc, doc_error = _doc_validations(doc)
            if doc_error:
                doc_errors += doc_error
                total_errors += 1
                continue
            partner, partner_error = _partner_validations(partner_ids, doc)
            if partner_error:
                partner_errors += partner_error
                total_errors += 1
                continue
            cfdi, attachment_error = read_cfdi_data(doc)
            if attachment_error:
                attachment_errors += attachment_error
                total_errors += 1
                continue
            lines, line_error = get_cfdi_lines(doc, cfdi, tax_ids, uom_ids)
            if line_error:
                line_errors += line_error
                total_errors += 1
                continue
            vals = {
                "partner_id": partner.id,
                "invoice_date": doc.date,
                "currency_id": doc.currency_id.id,
                "move_type": "out_invoice" if self.issuing_type == 'I' else 'in_invoice',
                "ref": "%s %s" % (doc.series, doc.number),
                "sat_document_id": doc.id,
            }
            if self.issuing_type == 'I':
                
                emisor_node = cfdi.Receptor
                cfdiuse = emisor_node.get("UsoCFDI", False)
                vals.update(
                    {
                        "l10n_mx_edi_payment_method_id": doc.payment_way_id.id,
                        "l10n_mx_edi_payment_policy": doc.payment_method,
                    }
                )
                if cfdiuse:
                    vals.update(
                        {
                            "l10n_mx_edi_usage": cfdiuse,
                        }
                    )
                    
            if doc.currency_id != self.env.company.currency_id:
                vals.update({"use_custom_rate": True, "custom_rate": doc.currency_rate})
            move_vals.append(vals)
            
            invoic = AccountMove.create(vals)
            for inv_lin in lines:
                inv_lin.update({'move_id': invoic.id})
                product = self.env["product.product"].browse(inv_lin['product_id'])
                inv_lin['product_uom_id'] = product.uom_id.id
                self.env['account.move.line'].create(inv_lin)
                
            for r in invoic:
                if r.move_type == 'out_invoice':
                    r.action_post()
                    r.l10n_mx_edi_cfdi_supplier_rfc = r.sat_document_id.company_id.partner_id.vat
                    r.l10n_mx_edi_cfdi_customer_rfc = partner.vat
                    r.l10n_mx_edi_cfdi_amount = r.sat_document_id.amount
                    r.l10n_mx_edi_cfdi_uuid = r.sat_document_id.name
                    cfdi_filename = ('%s-%s-MX-Invoice-3.3.xml' % (r.journal_id.code, r.name)).replace('/', '')
                    cfdi_attachment = self.env['ir.attachment'].create({
                        'name': cfdi_filename,
                        'res_id': r.id,
                        'res_model': r._name,
                        'type': 'binary',
                        'datas': r.sat_document_id.xml_attachment,
                        'mimetype': 'application/xml',
                        'description': _('Mexican invoice CFDI generated for the %s document.') % r.name,
                    })
                    
                    edi_document_vals_list = []
                    for edi_format in r.journal_id.edi_format_ids:
                        is_edi_needed = r.is_invoice(
                            include_receipts=False)
                        if is_edi_needed:
                            existing_edi_document = r.edi_document_ids.filtered(
                                lambda x: x.edi_format_id == edi_format)
                            if existing_edi_document:
                                existing_edi_document.write({
                                    'state': 'sent',
                                    'attachment_id': False,
                                })
                            else:
                                edi_document_vals_list.append({
                                    'move_id': r.id,
                                    'edi_format_id': edi_format.id,
                                    'attachment_id': cfdi_attachment.id,
                                    'state': 'sent',
                                })
                    self.env['account.edi.document'].create(edi_document_vals_list)
                    r.l10n_mx_edi_update_sat_status()
                    r.edi_state = 'sent'
                else:
                    r.l10n_mx_edi_cfdi_uuid_in_invoice = r.sat_document_id.name
                
        if doc_errors or partner_errors or attachment_errors or line_errors:
            raise UserError(
                _(
                    "There are %s errors on these documents:%s",
                    total_errors,
                    "".join(
                        error
                        for error in (
                            doc_errors,
                            partner_errors,
                            attachment_errors,
                            line_errors,
                        )
                        if error
                    ),
                )
            )
            
    def download_today_sat_documents(self):
        """Método para sincronizar los documentos emitidos en el día presente"""
        context_datetime = fields.Datetime.context_timestamp(
            self, fields.Datetime.now()
        )
        date_from = context_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
        self.env.company.download_cfdi_invoices(date_from, context_datetime)

    def range_sat_documents_action(self):
        """Método para abrir el wizard en donde se establece el rango de fechas para descarga de documentos"""
        return self.env["ir.actions.act_window"]._for_xml_id(
            "l10n_mx_sat_sync.sat_documents_range_download_action"
        )
