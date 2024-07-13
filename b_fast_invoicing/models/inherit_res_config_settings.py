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
# b_fast_invoicing

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    fi_notification_channel_ids = fields.Many2many(
        related='company_id.fi_notification_channel_ids',
        readonly=False
    )

    fi_generic_vat_number = fields.Char(
        string="Default Invoicing VAT",
        related='company_id.fi_generic_vat_number',
        readonly=False
    )
    fi_res_partner = fields.Many2one(
        'res.partner',
        'Default partner',
        related='company_id.fi_res_partner',
        readonly=False
    )
    define_time_create_invoice = fields.Selection(related='company_id.define_time_create_invoice')

    limit_days_to_invoice = fields.Integer(string="X Days",
                                           related='company_id.limit_days_to_invoice',
                                           readonly=False)
