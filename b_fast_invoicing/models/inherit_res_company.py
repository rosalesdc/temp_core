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
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    fi_notification_channel_ids = fields.Many2many(
        comodel_name='mail.channel',
        relation='website_channel_fast_invoicing_rel',
        column1='website_id',
        column2='channel_id',
        string='Notification channels'
    )
    
    fi_generic_vat_number = fields.Char(
        string="Default Invoicing VAT"
    )
    fi_res_partner = fields.Many2one(
        'res.partner',
        'Default partner'
    )
    
    define_time_create_invoice = fields.Selection([
        ('x_days', 'Make invoice x days after sale'),
        ('month', 'Make invoice in the same month'),
        ('not_deny', 'Do not set limit')
        ], "Picking Policy", default='not_deny')
    
    limit_days_to_invoice = fields.Integer(string="X Days")
    
    def get_state_id(self, country):
        val = []
        for r in self.env['res.country.state'].search([('country_id', '=', int(country))]):
            val.append((r.id, r.name))
        return val