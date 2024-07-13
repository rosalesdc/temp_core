from odoo import fields, models, api

class VexConfigSettings(models.Model):
    _name = "vex.config.settings"
    

    # Import
    store = fields.Selection([], string="Store")
    instance_id = fields.Many2one('vex.instance', string='Instance')
    
    frequency = fields.Selection([('always', 'Always'), ('once', 'Once')], string='Frequency')
    # Export 
    export_to = fields.Many2many('vex.instance', string='Export to?')
    export_stock = fields.Boolean('Stock export?')
    export_price = fields.Boolean('Price export?')


    
    