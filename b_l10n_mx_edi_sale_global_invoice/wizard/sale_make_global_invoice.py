# -*- encoding: utf-8 -*-
#
# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2024 Birtum - https://www.birtum.com
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
from odoo.fields import Command
import pytz
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

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


class SaleMakeGlobalInvoice(models.TransientModel):
    _name = 'sale.make.global.invoice'
    _description = 'Global Invoice creation from sale orders'

    date_from = fields.Date(
        string='Date from',
        help='Filter from date to get sale orders'
    )
    date_to = fields.Date(
        string='Date to',
        help='Filter end date to get sale orders'
    )
    team_id = fields.Many2one(
        comodel_name='crm.team',
        string="Sales Team",
        help='To be used as filter to search the orders by sale team.'
    )
    partner_id = fields.Many2one(
        'res.partner', 
        string='Invoice Customer',
        domain=[('vat', '=', 'XAXX010101000')],
        help='The partner for the invoice.'
    )
    sale_order_ids = fields.Many2many(
        'sale.order',
        compute='_get_sale_orders',
        string='Orders',
        help='Sale orders to generate the global invoice'
    )
    l10n_mx_edi_periodicidad = fields.Selection(
        selection=PERIODICIDAD,
        string='Periodicity',
        default='01',
        help='The period to which the global CFDI information.'
    )
    l10n_mx_edi_meses = fields.Selection(
        selection=MESES,
        string='Months',
        copy=False,
        help='Indicates the month or the months related to the CFDI global information.'
    )
    l10n_mx_edi_global_information_year = fields.Selection(
        selection=lambda self: self._get_global_information_year(),
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
    company_id = fields.Many2one(
        'res.company',
        required=True,
        default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id.id,
        required=True,
        help='Orders can have different currency, we have to filter by currency '
             'to create the correct invoice and avoid to mix currencies.'
    )
    l10n_mx_edi_payment_method_id = fields.Many2one(
        comodel_name='l10n_mx_edi.payment.method',
        string='Payment Way',
        help="Indicates the way the invoice was/will be paid, where the options could be: "
             "Cash, Nominal Check, Credit Card, etc. Leave empty if unkown and the XML will show 'Unidentified'."
    )

    @api.depends(
        'date_from',
        'date_to',
        'team_id',
        'currency_id',
        'l10n_mx_edi_payment_method_id'
    )
    def _get_sale_orders(self):
        domain = [
            ('state', 'in', ('sale', 'done')),
            ('invoice_status', '=', 'to invoice'),
            ('company_id', '=', self.company_id.id)]
        if self.date_from:
            initial_time = datetime.min.time()
            date_from = datetime.combine(self.date_from, initial_time)
            domain.extend([('date_order', '>=', date_from)])
        if self.date_to:
            ending_time = datetime.max.time()
            date_to = datetime.combine(self.date_to, ending_time)
            domain.extend([('date_order', '<=', date_to)])
        if self.team_id:
            domain.extend([('team_id', '=', self.team_id.id)])
        if self.currency_id:
            domain.extend([('currency_id', '=', self.currency_id.id)])
        if self.l10n_mx_edi_payment_method_id:
            domain.extend([('l10n_mx_edi_payment_method_id', '=', self.l10n_mx_edi_payment_method_id.id)])
        order_ids = self.env['sale.order'].search(domain)
        self.sale_order_ids = order_ids

    # for cfdi 4.0
    @api.depends('partner_id')
    def check_valid_partner_global_invoice(self):
        """
            validating if the partner and the VAT for the global invoice has the correct
            information that a global invoice requires.
        """
        for rec in self:
            rfc = rec.partner_id.commercial_partner_id.vat if rec.partner_id.commercial_partner_id.vat else ''
            partner_name = rec.partner_id.commercial_partner_id.name.upper() if rec.partner_id.commercial_partner_id and rec.partner_id.commercial_partner_id.name else ''
            if rfc == GENERAL_CUSTOMER[0] and partner_name == GENERAL_CUSTOMER[1]:
                rec.l10n_mx_edi_valid_global_partner_invoice = True
            else:
                rec.l10n_mx_edi_valid_global_partner_invoice = False

    # for cfdi 4.0
    def _get_global_information_year(self):
        """
            helps to get the current year and the past year to be available in options
            on the field: l10n_mx_edi_global_information_year
        """
        domain = []
        invoice_date = fields.Date.context_today(self)
        current_year = (str(invoice_date.year), str(invoice_date.year))
        domain.append(current_year)
        past_year = (str(invoice_date.year -1), str(invoice_date.year -1))
        domain.append(past_year)
        return domain

    @api.onchange('l10n_mx_edi_periodicidad')
    def _onchange_invoice_date(self):
        """
            based on current_date and l10n_mx_edi_periodicidad, we compute the 
            year and the month for the fields:
            - l10n_mx_edi_global_information_year
            - l10n_mx_edi_meses
        """
        invoice_date = fields.Date.context_today(self)
        invoice_year = invoice_date.year
        month = '%02d' % invoice_date.month
        if self.l10n_mx_edi_periodicidad and self.l10n_mx_edi_periodicidad == '05':
            month = BI.get(month)
        self.l10n_mx_edi_meses = month
        self.l10n_mx_edi_global_information_year = str(invoice_year)

    def action_invoice_generate(self):
        invoice_vals = self._prepare_invoice_vals()
        invoice_id = self.env['account.move'].sudo().with_company(self.company_id).with_context(
            default_move_type=invoice_vals['move_type']).create(invoice_vals)
        return {
            'name': _('Global invoice'),
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'context': "{'move_type': 'out_invoice', 'nodestroy': True}",
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': invoice_id.id,
        }

    def _prepare_invoice_vals(self):
        """
            prepare the invoice vals to create the global invoice.
            Args:
                payment_method_id (record): a record of pos.payment.method

            Returns:
                dict: dict with the vals to create the invoice.
        """
        self.ensure_one()
        invoice_date = fields.Date.context_today(self)
        timezone = pytz.timezone(self._context.get('tz') or self.env.user.tz or 'UTC')
        date_invoice = fields.Datetime.now()
        invoice_date = date_invoice.astimezone(timezone).date()
        invoice_line_vals, sale_line_vals = self._prepare_invoice_lines(self.sale_order_ids)
        l10n_mx_edi_payment_method_id = self._get_payment_method_global_invoice(sale_line_vals)
        vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_user_id': self.env.user.id,
            'invoice_date': invoice_date,
            'date': invoice_date,
            'invoice_line_ids': invoice_line_vals,
            'l10n_mx_edi_sale_global_lines': sale_line_vals,
            'invoice_payment_term_id': self.partner_id.property_payment_term_id.id or False,
            'l10n_mx_edi_periodicidad': self.l10n_mx_edi_periodicidad,
            'l10n_mx_edi_meses': self.l10n_mx_edi_meses,
            'l10n_mx_edi_payment_method_id': l10n_mx_edi_payment_method_id,
            'l10n_mx_edi_global_information_year': self.l10n_mx_edi_global_information_year,
            'l10n_mx_edi_global_invoice': True,
            'l10n_mx_edi_global_invoice_from_sales': True,
            'l10n_mx_edi_sale_global_invoice': True,
        }
        return vals

    @api.model
    def _prepare_invoice_lines(self, order_ids):
        invoiceable_lines = order_ids._get_invoiceable_lines(True)
        invoice_line_vals = [Command.create(line._prepare_invoice_line()) for line in invoiceable_lines]
        grouper = invoiceable_lines.mapped('order_id')
        grouped_lines = {order: invoiceable_lines.filtered(lambda x: x.order_id.id == order.id) for order in grouper}
        sale_line_vals = self._prepare_grouped_invoice_line(grouped_lines)
        return invoice_line_vals, sale_line_vals

    @api.model
    def _prepare_grouped_invoice_line(self, grouped_lines):
        """
            prepare an invoice line per order, including the amount total
            and taxes of the pos order.
            Args:
                order_id (record): a record of pos.order

            Returns:
                dict: dict with the vals to create an invoice line.
        """
        sale_line_vals = []
        for order_id, sale_line_ids in grouped_lines.items():
            # TODO
            # This field is in the module b_multiple_invoice pos, it has to be moved to the module
            # b_l10n_mx_edi_global_invoice.
            product_id = order_id.company_id.global_invoice_product_id or sale_line_ids[0].product_id
            subtotal = sum(sale_line_ids.mapped(lambda x: x.price_unit * x.qty_to_invoice))
            name = order_id.name
            sale_line_vals.append(
                Command.create(
                {
                    'name': name,
                    'product_id': product_id.id,
                    'quantity': 1,
                    'price_unit': subtotal,
                    'tax_ids': [],
                    'display_type': 'product',
                    'product_uom_id': product_id.uom_id.id,
                    'sale_order_id': order_id.id,
                    'l10n_mx_edi_global_sale_line_ids': sale_line_ids
                })
            )
        return sale_line_vals


    def _get_payment_method_global_invoice(self, sale_line_vals):
        """
            tool method to define the payment method for the global invoice,
            if the payment method is present at assistan, we take it and put on
            the invoice, otherwise we have to get sale order which has the highest amount
            :return: l10n_mx_edi_payment_method_id
        """
        if self.l10n_mx_edi_payment_method_id:
            return self.l10n_mx_edi_payment_method_id.id
        lst_dict = [dic[2] for dic in sale_line_vals]
        max_dic = max(lst_dict, key=lambda x: x['price_unit'])
        order_id = self.env['sale.order'].browse(max_dic['sale_order_id'])
        if order_id.l10n_mx_edi_payment_method_id:
            l10n_mx_edi_payment_method_id = order_id.l10n_mx_edi_payment_method_id.id
        else:
            l10n_mx_edi_payment_method_id = self.env.ref('l10n_mx_edi.payment_method_otros').id
        return l10n_mx_edi_payment_method_id