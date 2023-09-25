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
from odoo import models, fields, api

from datetime import datetime, timedelta


class AccountMove(models.Model):
    _inherit = 'account.move'

    payment_journal_id = fields.Many2one(
        'account.journal', string='Diario', compute='_compute_payment_journal_id', store=True)

    journal_id = fields.Many2one(
        'account.journal',
        string='Invoice Journal',
    )
    
    @api.depends('payment_state')
    def _compute_payment_journal_id(self):
        journal_obj = self.env['account.journal'].search([])
        for record in self:
            if record.state == 'posted' and record.invoice_payments_widget:
                journal_name = record.invoice_payments_widget['content'][0]['journal_name']
                journal = journal_obj.filtered(lambda p: p.name == journal_name)
                if journal:
                    record.payment_journal_id = journal[0].id
                else:
                    record.payment_journal_id = False
            else:
                record.payment_journal_id = False
