from odoo import fields, models, api

class VexProductPublications(models.Model):

    _name = 'vex.product.publications'

    publication_id = fields.Char(string="ID")
    publication_description = fields.Char(string="Description")
    publication_url = fields.Char(string="Permalink")
    publication_type = fields.Char(string="Type")
    publication_category = fields.Char(string="MELI Category")
    publication_price = fields.Char(string="MELI Price")
    product_id = fields.Many2one(comodel_name='product.template')
class productTemplate(models.Model):
    _inherit = 'product.template'

    publication_ids = fields.One2many(comodel_name= 'vex.product.publications', inverse_name='product_id', string='Publicaciones')