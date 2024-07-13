from odoo import api, fields, models

class VexProductAttribute(models.Model):
    _inherit         = "product.attribute"

    code = fields.Char('Código')
    store = fields.Selection([], string="Store")