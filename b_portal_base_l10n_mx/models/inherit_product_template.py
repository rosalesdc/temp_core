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

from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # TODO
    # 1. Create is_account_receivable_product field
    # 2. Create is_account_payable_product field
    # 3. In the view, is_account_receivable_product field visible
    #    if products = to sell.
    # 4. In the view, is_account_payable_product field visible
    #    if products = to purchase.
    # 5. Uncomment js view product input and set domain to show in popup
    #    [('is_account_receivable_product', '=', true), ('is_account_payable_product', '=', true)]
    # 6. In account.invoice, create a acumulator variable that keeps
    #    the amount sum and set to sent js product in to-add-line in invoice
    # 7. Search the customer by RFC value in CFDI.
    # 8. Add the CFDI to newly account.invoice record.

    is_account_receivable_product = fields.Boolean(
        string='Is receivable account product?',
        help='For inital load in receivable accounts.'
    )
    is_account_payable_product = fields.Boolean(
        string='Is payable account product?',
        help='For inital load in payable accounts.'
    )
