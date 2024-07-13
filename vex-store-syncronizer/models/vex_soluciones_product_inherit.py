from odoo import models, api, fields

class VexSolucionesProductInherit(models.Model):
    _inherit = 'product.template'
    
    action_export = fields.Selection([
        ('edit', 'Edition'),
        ('create', 'Creation')
    ], string='Action export', default="create")
    
    is_package = fields.Boolean('Is a Package?')
    product_unit_ids = fields.One2many('product.template.units', 'product_tmpl_id', string='product_unit')
    instance_ids = fields.Many2many('vex.instance', string='Instances')
    export_store = fields.Boolean('Export store?')
    
    
class InheritProductTemplateUnits(models.Model):
    _name = 'product.template.units'

    product_id = fields.Many2one('product.template', string='Product')
    meli_code = fields.Char('Publication ID')
    quantity = fields.Integer('Quantity')
    permalink = fields.Char('Permalink')
    product_tmpl_id = fields.Many2one('product.template', string='Product Template')