from odoo import fields, models, api

class VexSolucionesConfigSettingsInherit(models.Model):
    _inherit = "vex.config.settings"
    
    store = fields.Selection(selection_add=[('mercadolibre', 'Mercadolibre')])
    