# -*- encoding: utf-8 -*-

from odoo import models, fields, api


class AccountTax(models.Model):
    _inherit = "account.tax"

    tax_sat_code = fields.Char(string="Tax SAT Code")
