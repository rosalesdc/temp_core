# -*- encoding: utf-8 -*-
#
# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2021 Wedoo - http://www.wedoo.tech
# All Rights Reserved.
#
# Developer(s): Alan Guzmán
#               (age@wedoo.tech.com)
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


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    propose_payments = fields.Boolean(
        string='Propose payments',
        copy=False,
        default=False
    )


    @api.onchange(
        'payment_type',
        'partner_type',
        'partner_id',
        'journal_id',
        'currency_id',
        'amount',
        'created_from_invoice'
        )
    def onchange_partner_id(self):
        """
        This method creates/updates the payment lines when a parner_id is selected,
        when the currency changes the payment amount is applied into line amounts
        """
        # TODO
        # the lines won't be computed if the payment is created from an invoice
        super(AccountPayment, self).onchange_partner_id()
        if self.propose_payments:
            if self.created_from_invoice:
                self.payment_line_ids = []
            else:
                self.payment_line_ids = self.recompute_payment_lines()
                amount_payment = self.amount
                for line in self.payment_line_ids.sorted('amount_unreconciled'):
                    if amount_payment > line.amount_unreconciled:
                        line.amount = line.amount_unreconciled
                        amount_payment -= line.amount_unreconciled
                        line.reconcile = True
                    elif amount_payment == line.amount_unreconciled:
                        line.amount = amount_payment
                        amount_payment -= line.amount_unreconciled
                        line.reconcile = True
                    else:
                        line.amount = amount_payment
                        amount_payment = 0.0
        else:
            if self.created_from_invoice:
                self.payment_line_ids = []
            else:
                self.payment_line_ids = self.recompute_payment_lines()