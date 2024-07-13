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
from odoo import models, fields
from lxml import etree
from datetime import datetime
from odoo.exceptions import UserError



class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    def _l10n_mx_edi_get_invoice_cfdi_global_invoice_values(self, invoice):
        """
            tool method to generate the required vals for the CFDI of Factura global.
            Args:
                invoice (account.move): the invoice to generate the CFDI

            Returns:
                dict: dict vals to render the qweb template to generate the CFDI(XML)
        """
        if invoice.invoice_date >= fields.Date.context_today(self) and invoice.invoice_date == invoice.l10n_mx_edi_post_time.date():
            cfdi_date = invoice.l10n_mx_edi_post_time.strftime('%Y-%m-%dT%H:%M:%S')
        else:
            cfdi_time = datetime.strptime('23:59:00', '%H:%M:%S').time()
            cfdi_date = datetime.combine(
                fields.Datetime.from_string(invoice.invoice_date),
                cfdi_time
            ).strftime('%Y-%m-%dT%H:%M:%S')

        cfdi_values = {
            **invoice._prepare_edi_global_invoice_vals_to_export(),
            **self._l10n_mx_edi_get_common_cfdi_values(invoice),
            'document_type': 'I' if invoice.move_type == 'out_invoice' else 'E',
            'currency_name': invoice.currency_id.name,
            'payment_method_code': (invoice.l10n_mx_edi_payment_method_id.code or '').replace('NA', '99'),
            'payment_policy': invoice.l10n_mx_edi_payment_policy,
            'cfdi_date': cfdi_date,
            'l10n_mx_edi_external_trade_type': '01', # CFDI 4.0
        }

        # ==== Invoice Values ====
        if invoice.currency_id.name == 'MXN':
            cfdi_values['currency_conversion_rate'] = None
        else:  # assumes that invoice.company_id.country_id.code == 'MX', as checked in '_is_required_for_invoice'
            cfdi_values['currency_conversion_rate'] = abs(invoice.amount_total_signed) / abs(invoice.amount_total) if invoice.amount_total else 1.0

        if invoice.partner_bank_id:
            digits = [s for s in invoice.partner_bank_id.acc_number if s.isdigit()]
            acc_4number = ''.join(digits)[-4:]
            cfdi_values['account_4num'] = acc_4number if len(acc_4number) == 4 else None
        else:
            cfdi_values['account_4num'] = None

        if cfdi_values['customer'].country_id.l10n_mx_edi_code != 'MEX' and cfdi_values['customer_rfc'] not in ('XEXX010101000', 'XAXX010101000'):
            cfdi_values['customer_fiscal_residence'] = cfdi_values['customer'].country_id.l10n_mx_edi_code
        else:
            cfdi_values['customer_fiscal_residence'] = None

        # ==== Tax details ====

        def get_tax_cfdi_name(tax_detail_vals):
            tags = set()
            for detail in tax_detail_vals['group_tax_details']:
                for tag in detail['tax_repartition_line'].tag_ids:
                    tags.add(tag)
            tags = list(tags)
            if len(tags) == 1:
                return {'ISR': '001', 'IVA': '002', 'IEPS': '003'}.get(tags[0].name)
            elif tax_detail_vals['tax'].l10n_mx_tax_type == 'Exento':
                return '002'
            else:
                return None

        global_taxes = invoice._get_global_taxes()
        cfdi_values.update({
            'get_tax_cfdi_name': get_tax_cfdi_name,
            'tax_details_transferred': global_taxes,
        })
        cfdi_values.update({
            'has_tax_details_transferred_no_exento': any(x['tax'].l10n_mx_tax_type != 'Exento' for x in cfdi_values['tax_details_transferred']['tax_details'].values()),
            'has_tax_details_withholding_no_exento': False,
        })
        # Recompute Totals since lines changed.
        cfdi_values.update({
            'total_price_subtotal_before_discount': sum(x['price_subtotal_before_discount'] for x in cfdi_values['invoice_line_vals_list']),
            'total_price_discount': sum(x['price_discount'] for x in cfdi_values['invoice_line_vals_list']),
        })
        cfdi_values.update(self._l10n_mx_edi_get_40_values(invoice))
        total_tax = global_taxes['tax_amount_currency']
        amount_total = sum(invoice.l10n_mx_edi_sale_global_lines.mapped('price_total'))
        subtotal_invoice = cfdi_values['total_price_subtotal_before_discount'] if cfdi_values['tax_objected'] == '02' else amount_total + cfdi_values['total_price_discount']
        total_invoice = subtotal_invoice + total_tax
        cfdi_values['subtotal_invoice'] = subtotal_invoice
        cfdi_values['total_invoice'] = total_invoice
        return cfdi_values


    def _l10n_mx_edi_export_invoice_cfdi(self, invoice):
        ''' Create the CFDI attachment for the invoice passed as parameter.

        :param move:    An account.move record.
        :return:        A dictionary with one of the following key:
        * cfdi_str:     A string of the unsigned cfdi of the invoice.
        * error:        An error if the cfdi was not successfuly generated.
        '''


        # == CFDI values ==
        if invoice.l10n_mx_edi_global_invoice:
            if invoice.l10n_mx_edi_global_invoice_from_sales and invoice.l10n_mx_edi_sale_global_lines:
                cfdi_values = self._l10n_mx_edi_get_invoice_cfdi_global_invoice_values(invoice)
                qweb_template, xsd_attachment_name = self._l10n_mx_edi_get_invoice_global_invoice_templates()
            else:
                cfdi_values = self._l10n_mx_edi_get_invoice_cfdi_values(invoice)
                qweb_template, xsd_attachment_name = self._l10n_mx_edi_get_invoice_templates()
            # == Generate the CFDI ==
            cfdi = self.env['ir.qweb']._render(qweb_template, cfdi_values)
            decoded_cfdi_values = invoice._l10n_mx_edi_decode_cfdi(cfdi_data=cfdi)
            cfdi_cadena_crypted = cfdi_values['certificate'].sudo()._get_encrypted_cadena(decoded_cfdi_values['cadena'])
            decoded_cfdi_values['cfdi_node'].attrib['Sello'] = cfdi_cadena_crypted

            res = {
                'cfdi_str': etree.tostring(decoded_cfdi_values['cfdi_node'], pretty_print=True, xml_declaration=True, encoding='UTF-8'),
            }
            try:
                self.env['ir.attachment'].l10n_mx_edi_validate_xml_from_attachment(decoded_cfdi_values['cfdi_node'], xsd_attachment_name)
            except UserError as error:
                res['errors'] = str(error).split('\\n')
            return res
        return super(AccountEdiFormat, self)._l10n_mx_edi_export_invoice_cfdi(invoice)



    def _l10n_mx_edi_get_invoice_global_invoice_templates(self):
        """
            tool method to return the template that is used to generate a CFDI
            of Factura global.
            Returns:
                tuple: names of files
        """
        return 'b_l10n_mx_edi_global_invoice.global_cfdi40', 'cfdv40.xsd'