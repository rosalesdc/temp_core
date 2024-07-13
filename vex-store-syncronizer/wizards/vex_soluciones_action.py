from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

class VexSolucionesAction(models.TransientModel):
    _name = "vex.import.wizard"
    _description = "Wizard Model to trigger import/update actions"
    
    
    store = fields.Selection([], string="Store")
    instance_id = fields.Many2one('vex.instance', string='Instance')
    
    @api.onchange('store')
    def _onchange_store(self):
        pass

    def synchronize(self):
        if not self.store:
            raise ValidationError("Selecting a store is mandatory.")
        if not self.instance_id:
            raise ValidationError("Selecting an instance is mandatory.")