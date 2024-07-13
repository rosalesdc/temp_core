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

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProviderInfo(models.Model):
    _name = "product.provider.info"
    _description = "Products Provider information"

    partner_id = fields.Many2one("res.partner", string="Provider.")
    product_sku = fields.Char(string="SKU", help="SKU for this product and this provider.")

    @api.model_create_multi
    def create(self, vals, **kwargs):
        self.validate_sku(vals)
        return super(ProviderInfo, self).create(vals)

    def write(self, vals):

        self.validate_sku([vals])
        return super(ProviderInfo, self).write(vals)

    def validate_sku(self, vals_list):
        for vals in vals_list:
            sku = vals.get("product_sku", self.product_sku)
            partner = vals.get("partner_id", self.partner_id.id)
        if self.existing_product(sku, partner):
            raise ValidationError(_("The SKU and partner already exist."))
        return True

    def existing_product(self, sku, partner):
        return bool(self.search(["&", ("product_sku", "=", sku), ("partner_id", "=", partner)]))


class ProductProviderInfo(models.Model):
    _inherit = "product.product"

    provider_ids = fields.Many2many("product.provider.info", string="Provider Information", help="Provider information for this product.")
