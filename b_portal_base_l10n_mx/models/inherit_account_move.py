# -*- encoding: utf-8 -*-
#
# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2023 Birtum - http://www.birtum.com
# All Rights Reserved.
#
# Developer(s): Carlos Maykel López González
#               (clg@birtum.com)
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

import os
import re
import base64
import datetime
import tempfile
import requests
from lxml import etree, objectify
from lxml.objectify import fromstring
from io import BytesIO

from . import XmlTools

from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero
from odoo.fields import Date
from odoo.addons import decimal_precision as dp
from odoo.tools.xml_utils import _check_with_xsd

CFDI_SAT_QR_STATE = {
    'No Encontrado': 'not_found',
    'Cancelado': 'cancelled',
    'Vigente': 'valid',
}

MODULE_EXTRA_NAME = "transfer_utils_purchase_addons"


class AccountInvoice(models.Model):
    _inherit = "account.move"

    l10n_mx_edi_cfdi_uuid = fields.Char(string='Fiscal Folio', copy=False, readonly=True, store=True,
                                        help='Folio in electronic invoice, is returned by SAT when send to stamp.')

    fiscal_folio = fields.Char(string="FOLIO FISCAL")

    @api.model
    def create_from_xml_sat(self, xml_sat):
        """
        Creates an account move with a XML, take different types of nodes and
        map to odoo fields,
        Arguments:
            attachments {list} -- List of attachments (CFDI's) 
            purchase_order {purchase.order} -- Purchase order to link
        Raises:
            Exception: If not a res.partner in odoo
        Returns:
            list -- List with number of CFDI's Created, RFC rejected (if not in odoo) , created invoice, file name of invoice
        """
        date_invoice = xml_sat.get_date()
        company = self.env.user.company_id
        partner, is_you_sender = self.get_partner(xml_sat)

        # if xml_sat.xml_type == 'is_provider':
        #     self.check_extra_module()

        new_invoice = None
        invoice_lines = self.create_invoice_lines(xml_sat.get_concepts(), xml_sat)
        # Get account jounal
        journal = self.env['account.journal'].search([
            ('type', '=', 'sale' if is_you_sender else 'purchase'),
            ('company_id', '=', company.id)
        ], limit=1)

        invoice_vals = {
            'partner_id': partner.id,
            'move_type': 'out_invoice' if is_you_sender else 'in_invoice',
            'invoice_line_ids': invoice_lines,
            'journal_id': journal.id if journal else self._default_journal().id,
            'invoice_date': Date.from_string(date_invoice)
        }

        invoice_vals.update(self.set_cfdi_values(xml_sat))
        new_invoice = self.create(invoice_vals)
        attachment = new_invoice.attach_xml(xml_sat.b64_file)
        """
        new_invoice.write({
            'l10n_mx_edi_cfdi_name': attachment.name
        })
        """
        uuid = xml_sat.get_uuid()
        try:
            new_invoice.write({'l10n_mx_edi_cfdi_uuid': uuid})
        except:
            pass
        return (new_invoice, attachment.name)

    def get_partner(self, xml_sat):
        rfc_sender = xml_sat.get_supplier_vat()
        rfc_receiver = xml_sat.get_customer_vat()
        is_you_sender = (rfc_sender == self.env.user.company_id.partner_id.vat)
        rfc_to_search = rfc_receiver if is_you_sender else rfc_sender
        partner = self.env['res.partner'].search([
            ('vat', '=', rfc_to_search)
        ], limit=1)
        if not partner:
            raise ValidationError(_("The VAT '%s' does not match in the system.") % rfc_to_search)
        return partner, is_you_sender

    # def check_extra_module(self):
    #     extra_module = self.env['ir.module.module'].search([('name','=',MODULE_EXTRA_NAME)])
    #     error_message = """
    #     For provider invoice is necessary install the module %s
    #     or activate the extra option in Settings/Accounting/Transfer Utils
    #     """
    #     error_message = error_message.replace("\n","")
    #     if not extra_module.state == 'installed':
    #         raise ValidationError(_(error_message)%MODULE_EXTRA_NAME)

    def create_invoice_lines(self, concepts, xml_sat):
        invoice_lines = []
        for concept in concepts:
            invoice_lines.append(self.create_invoice_line(concept, xml_sat))
        return invoice_lines

    def create_invoice_line(self, concept, xml_sat):
        """
        Take the concept data an map to odoo fields
        Arguments:
            concepts {dict} -- Concepts of CFDI
        Raises:
            Exception: No existe ningun producto con la clave XXXXX SAT en el sistema."
            Exception: No existe ningun producto que coincida con la clave del producto
            Exception: Las lineas de la factura no corresponden con las del XML
            Exception: Existe mas de un producto XXXX en el sistema.en el sistema.
        Returns:
            list -- invoice lines related to a account move
        """
        invoice_dict = xml_sat.get_concept_dict(concept)
        product = self.get_product_from_concept(invoice_dict, xml_sat.xml_type, xml_sat)
        _, is_you_sender = self.get_partner(xml_sat)
        invoice_line_vals = {
            'account_id': product.product_tmpl_id._get_product_accounts().get(
                'income').id if is_you_sender else product.product_tmpl_id._get_product_accounts().get('expense').id,
            'product_id': product.id,
            'name': product.name,
            'price_unit': invoice_dict.get("price_unit", 0.0),
            'quantity': invoice_dict.get("quantity", 0.0)}
        descuento = invoice_dict.get("discount", 0.0)
        v_unitario = invoice_dict["price_unit"]
        if descuento != 0.0:
            invoice_line_vals['discount'] = (float(descuento) / float(v_unitario)) * 100.0
        invoice_line_vals['tax_ids'] = self.set_taxes(concept, xml_sat)
        return [0, False, invoice_line_vals]

    def get_product_from_concept(self, invoice_dict, invoice_type, xml_sat):
        if invoice_type == 'is_client':
            return self.get_product_from_concept_client(invoice_dict)
        return self.get_product_from_concept_provider(invoice_dict, xml_sat)

    def get_product_from_concept_client(self, invoice_dict):
        product = False
        p_num = False
        if invoice_dict.get("default_code", '') != '':
            p_num = invoice_dict["default_code"]
            product = self.env['product.product'].search([('default_code', '=', invoice_dict["default_code"])])
        elif invoice_dict.get("sat_code", '') != '':
            product = self.env['product.product'].search([('unspsc_code_id.code', '=', invoice_dict["sat_code"])])
            p_num = invoice_dict["sat_code"]
            if not product:
                raise ValidationError(_("The product with the key '%s' SAT does not exist in the system.") % str(invoice_dict["sat_code"]))
        else:
            raise ValidationError(_("There is no product that matches the product key"))
        if not product:
            raise ValidationError(_("There is no product %s in the system.") % str(p_num))
        if len(product) > 1:
            raise ValidationError(_("There is more than one product %s in the system.") % str(p_num))
        return product

    def get_product_from_concept_provider(self, invoice_dict, xml_sat):
        product = False
        p_num = False
        partner, _none = self.get_partner(xml_sat)
        if invoice_dict.get("default_code", '') != '':
            p_num = invoice_dict["default_code"]
            domain = ["&", ('product_sku', '=', invoice_dict["default_code"]), ("partner_id", "=", partner.id)]
            product_supplier = self.env['product.provider.info'].search(domain)
            if product_supplier:
                product = self.env["product.product"].search([("provider_ids", "in", [product_supplier.id])])

        elif invoice_dict.get("sat_code", '') != '':
            product = self.env['product.product'].search([('unspsc_code_id.code', '=', invoice_dict["sat_code"])])
            p_num = invoice_dict["sat_code"]
            if not product:
                raise ValidationError(_("The product with the key '%s' SAT does not exist in the system.") % str(invoice_dict["sat_code"]))
        else:
            raise ValidationError(_("There is no product that matches the product key"))

        if not product:
            raise ValidationError(_("There is no product %s in the system with provider %s.") % (str(p_num), partner.name))
        if len(product) > 1:
            raise ValidationError(_("There is more than one product %s in the system.") % str(p_num))
        return product

    def set_taxes(self, concept, xml_sat):
        """
        Get taxes info for each concept in XML
        
        Arguments:
            concept {dict} -- Related concept        
        Raises:
            Exception: El impuesto YYY no existe en el sistema. Agregue el código al impuesto si es necesario. If tax search is null
        """
        taxes = xml_sat.get_concept_taxes(concept)
        is_you_sender = (xml_sat.get_supplier_vat() == self.env.user.company_id.partner_id.vat)
        taxes_ids = []
        for tax in taxes:
            tax_dict = xml_sat.get_tax_dict(tax)
            if tax_dict.get('factor').lower() == 'exento':
                tax_dict["amount"] = 0.0
            type_tax_use = 'sale' if is_you_sender else 'purchase'
            tax = self.env['account.tax'].search([
                ('tax_sat_code', '=', tax_dict["sat_tax_code"]),
                ('amount', '=', float(tax_dict["amount"]) * 100.0),
                ('l10n_mx_tax_type', '=', tax_dict.get("factor", "").capitalize()),
                ('type_tax_use', '=', type_tax_use)])
            if len(tax) > 1:
                tax = tax[0]
            if not tax:
                raise ValidationError(_("Tax %s whit rate %s does not exist in the system. Add the code to the tax if necessary.") % (
                    tax_dict["sat_tax_code"], tax_dict["amount"]))
            taxes_ids.append(tax.id)
        return [(6, 0, taxes_ids)]

    @api.model
    def _default_journal(self):
        journal_type = self.env.context.get('journal_type', False)
        company_id = self.env.company.id
        if journal_type:
            journals = self.env['account.journal'].search([('type', '=', journal_type), ('company_id', '=', company_id)])
            if journals:
                return journals[0]
        return self.env['account.journal']

    def set_cfdi_values(self, xml_sat):
        """
        Map XML data with odoo fields
        Arguments:
            xml_sat {XmlSatTools} -- XML data        
        Returns:
            dict -- CFDI information 
        """
        cfdi_vals = {}
        m_pago = self.env['l10n_mx_edi.payment.method'].search([('code', '=', xml_sat.get_payment_form())])
        if m_pago:
            cfdi_vals['l10n_mx_edi_payment_method_id'] = m_pago.id
        if xml_sat.get_cfdi_use() != '':
            cfdi_vals['l10n_mx_edi_usage'] = xml_sat.get_cfdi_use()
        if xml_sat.get_payment_method() != '':
            cfdi_vals['l10n_mx_edi_payment_policy'] = xml_sat.get_payment_method()
        return cfdi_vals

    def get_number_xml_attached(self):
        n_attach = 0
        attachments = self.env['ir.attachment'].search(['&', ('res_id', '=', self.id),
                                                        ('res_model', '=', 'account.move')])
        if attachments:
            attachments = attachments.filtered(lambda a: a.name.lower().endswith(".xml"))
            n_attach = len(attachments)
        return n_attach

    def attach_xml(self, data):
        """
        Create a ir attachment with XML data
        Arguments:
            data {str} -- xml content encoded in b64
        Returns:
            [type] -- [description]
        """
        new_filename = ('%s-%s-MX-Invoice-%s.xml' % (
            self.journal_id.code,
            self.id,
            "3-3")).replace('/', '')
        attachment_vals = {
            'name': new_filename,  # instead ofxml_pair[1], xml filename
            'datas': data,  # base64 string
            'store_fname': new_filename,
            'res_model': 'account.move',
            'res_id': self.id
        }
        return self.env['ir.attachment'].create(attachment_vals)

    def create_attachment_from_file(self, new_invoice, data):
        """
        Create a ir attachment with XML data
        Arguments:
            new_invoice {account.move} -- related invoice
            data {str} -- xml content encoded in b64
        Returns:
            [type] -- [description]
        """
        new_filename = ('%s-%s-MX-Invoice-%s.xml' % (
            self.journal_id.code,
            self.id,
            "3-3")).replace('/', '')
        attachment_vals = {
            'name': new_filename,  # instead ofxml_pair[1], xml filename
            'datas': data,  # base64 string
            'store_fname': new_filename,
            'res_model': 'account.move',
            'res_id': new_invoice.id
        }
        return self.env['ir.attachment'].create(attachment_vals)
