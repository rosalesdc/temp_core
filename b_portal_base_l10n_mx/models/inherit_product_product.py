# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def get_product_displayname(self, product_id):
        """ Returns product displayname for js views """
        if product_id:
            return self.search([("id", "=", product_id)], limit=1).name
        else:
            return _("DN: None for selected product ...")
