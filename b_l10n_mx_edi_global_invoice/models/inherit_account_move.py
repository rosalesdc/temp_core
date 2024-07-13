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
from odoo import models, fields, api, _
from collections import defaultdict
from odoo.exceptions import ValidationError

# TODO
# this var is used to validate if the node: InformacionGlobal has to be present
# at CFDI
GENERAL_CUSTOMER = ['XAXX010101000', 'PUBLICO EN GENERAL']

PERIODICIDAD = [
    ('01', 'Daily'),
    ('02', 'Weekly'),
    ('03', 'Biweekly'),
    ('04', 'Monthly'),
    ('05', 'Bimonthly')
]
MESES = [
    ('01', 'January'),
    ('02', 'February'),
    ('03', 'March'),
    ('04', 'April'),
    ('05', 'May'),
    ('06', 'June'),
    ('07', 'July'),
    ('08', 'August'),
    ('09', 'September'),
    ('10', 'October'),
    ('11', 'November'),
    ('12', 'December'),
    ('13', 'January-February'),
    ('14', 'March-April'),
    ('15', 'May-June'),
    ('16', 'July-August'),
    ('17', 'September-October'),
    ('18', 'November-December')
]

BI = {
    '01': '13',
    '02': '13',
    '03': '14',
    '04': '14',
    '05': '15',
    '06': '15',
    '07': '16',
    '08': '16',
    '09': '17',
    '10': '17',
    '11': '18',
    '12': '18'
}


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_mx_edi_global_invoice = fields.Boolean(
        string='Global invoice',
        copy=False,
        help='Indicates that the document is a global invoice'
    )
    l10n_mx_edi_periodicidad = fields.Selection(
        selection=PERIODICIDAD,
        string='Periodicity',
        help='the period to which the global CFDI information.'
    )
    l10n_mx_edi_meses = fields.Selection(
        selection=MESES,
        string='Months',
        copy=False,
        help='Indicates the month or the months related to the CFDI global information.'
    )
    l10n_mx_edi_global_information_year = fields.Selection(
        '_get_global_information_year',
        string='Year',
        help='The value of this field must be equal to the current year or the '
             'immediately previous year. For validating the current year or the '
             'immediately preceding year should be considered the one registered in the invoice date.'
    )
    l10n_mx_edi_valid_global_partner_invoice = fields.Boolean(
        string='Valid partner',
        compute='check_valid_partner_global_invoice',
        help='The selected partner has to be consistent with the partner that a global invoice requires'
    )
    l10n_mx_edi_sale_global_lines = fields.One2many(
        'global.invoice.line',
        'move_id',
        copy=False,
        readonly=True,
    )
    l10n_mx_edi_global_invoice_from_sales = fields.Boolean()

    # for cfdi 4.0
    @api.depends('partner_id', 'l10n_mx_edi_global_invoice')
    def check_valid_partner_global_invoice(self):
        """
            validating if the partner and the VAT for the global invoice has the correct
            information that a global invoice requires.
        """
        for invoice in self:
            if invoice.l10n_mx_edi_global_invoice:
                rfc = invoice.partner_id.commercial_partner_id.vat if invoice.partner_id.commercial_partner_id.vat else ''
                partner_name = invoice.partner_id.commercial_partner_id.name.upper() if invoice.partner_id.commercial_partner_id and invoice.partner_id.commercial_partner_id.name else ''
                if rfc == GENERAL_CUSTOMER[0] and partner_name == GENERAL_CUSTOMER[1]:
                    invoice.l10n_mx_edi_valid_global_partner_invoice = True
                else:
                    invoice.l10n_mx_edi_valid_global_partner_invoice = False
            else:
                invoice.l10n_mx_edi_valid_global_partner_invoice = False

    # for cfdi 4.0
    def _get_global_information_year(self):
        """
            helps to get the current year and the past year to be available in options
            on the field: l10n_mx_edi_global_information_year
        """
        domain = []
        invoice_date = self.invoice_date or fields.Date.context_today(self)
        current_year = (str(invoice_date.year), str(invoice_date.year))
        domain.append(current_year)
        past_year = (str(invoice_date.year -1), str(invoice_date.year -1))
        domain.append(past_year)
        return domain

    @api.onchange(
        'invoice_date',
        'l10n_mx_edi_periodicidad'
    )
    def _onchange_invoice_date(self):
        """
            updating fields base on invoice_date and l10n_mx_edi_periodicidad, we compute the 
            year and the month for the fields:
            - l10n_mx_edi_global_information_year
            - l10n_mx_edi_meses
        """

        today = fields.Date.context_today(self)
        invoice_date = self.invoice_date or today
        invoice_year = invoice_date.year
        current_year = today.year
        if invoice_year > current_year:
            return {'warning': {
                    'title': _('Invoice year'),
                    'message': 'The year of the invoice date is higher than current year, '
                               'that is a problem to compute the global information year for the '
                               'global invoice, please selected the correct invoice date.'
                }}
        month = '%02d' % invoice_date.month
        if self.l10n_mx_edi_periodicidad and self.l10n_mx_edi_periodicidad == '05':
            month = BI.get(month)
        self.l10n_mx_edi_meses = month
        self.l10n_mx_edi_global_information_year = str(invoice_year)


    def action_post(self):
        """
            inherited method in order to validate if the invoice partner has the correct
            information required for the CFDI, when the invoice is marked as a global invoice.
        """
        res = super(AccountMove, self).action_post()
        for move in self:
            if move.l10n_mx_edi_global_invoice and not move.l10n_mx_edi_valid_global_partner_invoice:
                raise ValidationError(_(
                    'The invoice cannot be post, due to the selected partner does not have the correct information '
                    'required for the CFDI, check the warning message and select a correct partner or fix the information.'))
        return res


    @api.model
    def _get_tax_type(self, tax_id, tax):
        """
            aux method to get the rate of the tax
            Args:
                tax_id (account.tax): a record of account.tax model
                tax (dict): dict vals of taxes.

            Returns:
                _type_: _description_
        """
        if tax_id.l10n_mx_tax_type == 'Tasa':
            return (tax_id.amount / 100.0)
        elif tax_id.l10n_mx_tax_type == 'Cuota':
            return (tax['tax_amount_currency'] / tax['base_amount_currency'])
        else:
            return None


    def _prepare_edi_global_invoice_vals_to_export(self):
        """
            tool method to return strategic vals for the CFDI of factura global,
            we prepared the invoice lines used at conceptos of the CFDI
            Returns:
                _type_: _description_
        """
        self.ensure_one()

        res = {
            'record': self,
            'balance_multiplicator': -1 if self.is_inbound() else 1,
            'invoice_line_vals_list': [],
        }
        # Invoice lines details.
        for index, line in enumerate(self.l10n_mx_edi_sale_global_lines.filtered(lambda line: line.display_type == 'product'), start=1):
            line_vals = line._prepare_edi_global_invoice_vals_to_export()
            line_vals['index'] = index
            res['invoice_line_vals_list'].append(line_vals)

        # Totals.
        res.update({
            'total_price_subtotal_before_discount': sum(x['price_subtotal_before_discount'] for x in res['invoice_line_vals_list']),
            'total_price_discount': sum(x['price_discount'] for x in res['invoice_line_vals_list']),
        })

        return res

    def _get_global_taxes(self):
        """
            aux method that helps to get the taxes of all pos orders related to
            invoice lines and accumulated in groups, to be used in the CFDI.
            we have only support Traslados.
            Returns:
                dict: dict global taxes vals.
        """
        self.ensure_one()
        grouped_taxes = {
                'tax_amount_currency': 0.0,
                'tax_details': defaultdict(lambda: {
                    'base_amount_currency': 0.0,
                    'base_amount': 0.0,
                    'tax_amount_currency': 0.0,
                    'tax_amount': 0.0,
                })
            }
        if any(x.has_global_taxes for x in self.l10n_mx_edi_sale_global_lines):
            invoice_line_ids = self.l10n_mx_edi_sale_global_lines.filtered(lambda inv: inv.has_global_taxes)
            sale_global_taxes = invoice_line_ids.mapped('sale_grouped_taxes')
            for sale_tax in sale_global_taxes:
                for tax in sale_tax['tax_details'].values():
                    key = tax['tax']
                    if key not in grouped_taxes['tax_details']:
                        grouped_taxes['tax_details'][key] = {
                            'tax': tax['tax'],
                            'base_amount': tax['base_amount'],
                            'tax_amount': tax['tax_amount'],
                            'base_amount_currency': tax['base_amount_currency'],
                            'tax_amount_currency': tax['tax_amount_currency'],
                            'tax_rate_transferred': tax['tax_rate_transferred'],
                            'group_tax_details': tax['group_tax_details']
                        }
                    else:
                        grouped_taxes['tax_details'][key].update({
                            'base_amount': grouped_taxes['tax_details'][key]['base_amount'] + tax['base_amount'],
                            'tax_amount': grouped_taxes['tax_details'][key]['tax_amount'] + tax['tax_amount'],
                            'base_amount_currency': grouped_taxes['tax_details'][key]['base_amount_currency'] + tax['base_amount_currency'],
                            'tax_amount_currency': grouped_taxes['tax_details'][key]['tax_amount_currency'] + tax['tax_amount_currency'],
                        })
                    grouped_taxes['tax_amount_currency'] += tax['tax_amount_currency']
        return grouped_taxes


