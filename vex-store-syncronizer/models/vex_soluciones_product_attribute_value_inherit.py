from odoo import models, fields, api

class VexSolcuionesProductAttributeValueInherit(models.Model):
    _inherit= "product.attribute.value"
    
    sku = fields.Char('Sku')