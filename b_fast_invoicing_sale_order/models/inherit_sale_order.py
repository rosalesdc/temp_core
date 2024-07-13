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

import json
import logging
import random
import string
from psycopg2 import OperationalError

from datetime import timedelta

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError

from werkzeug import urls

_logger = logging.getLogger('[ AUTO FACTURA ]')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    invoicing_ref = fields.Char()
    service_effective_date = fields.Datetime(
        compute='_compute_service_effective_date',
        store=True, copy=False
    )
    from_auto_invoice = fields.Boolean()

    def get_invoicing_url(self):
        """

        :return:
        """
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].with_user(SUPERUSER_ID).get_param(
            'web.base.url')
        return urls.url_join(base_url, "/autofactura/client")
    
    @api.depends('order_line', 'order_line.product_id', 'date_order')
    def _compute_service_effective_date(self):
        for record in self:
            if any(line.product_id.type != 'service' for line in record.order_line):
                record.service_effective_date = False
            else:
                record.service_effective_date = record.date_order

    def generate_invoicing_ref(self):
        """
        Generate invoicing ref unique code.
        :return:
        """
        self.ensure_one()
        if self.invoicing_ref:
            return False
        reference = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        return self.write({'invoicing_ref': reference})

    @api.model_create_multi
    def create(self, vals_list):
        order = super(SaleOrder, self).create(vals_list)
        for res in order:
            res.with_user(SUPERUSER_ID).generate_invoicing_ref()
        return order
    
    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        if 'invoicing_ref' not in vals:
            for order in self:
                order.generate_invoicing_ref()
        return res

    def get_invoicing_url(self):
        self.ensure_one()
        base_url = self.get_base_url()
        return urls.url_join(base_url, "/autofactura/client")

    def _prepare_invoice(self):
        self.ensure_one()
        res = super(SaleOrder, self)._prepare_invoice()
        if self.env.context.get('allow_use_generic_vat', False):
            res['auto_invoice_vat'] = self.env.context['allow_use_generic_vat']
        if self.env.context.get('allow_use_generic_partner', False):
            res['auto_invoice_partner'] = self.env.context['allow_use_generic_partner']
        res['from_auto_invoice'] = self.env.context.get('from_auto_invoice', False)
        return res

    def fi_action_send_error(self, error):
        channels = self.env.user.company_id.fi_notification_channel_ids
        message_obj = self.env['mail.message']
        if channels:
            message_obj.create({
                'author_id': self.partner_id.id,
                'model': 'mail.channel',
                'res_id': 0,
                'message_type': 'comment',
                'body': _('Error auto invoicing SO {}. {}').format(self.name, error),
                'channel_ids': [(6, 0, channels.ids)]
            })
        return True
