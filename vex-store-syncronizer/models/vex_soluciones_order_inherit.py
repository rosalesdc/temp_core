from odoo import api, fields, models

class VexSolucionesOrderInherit(models.Model):
    _inherit = "sale.order"
    
    instance_id = fields.Many2one('vex.instance', string='Instance')