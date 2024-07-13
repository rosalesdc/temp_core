from odoo import fields, models, api

class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'
    
    meli_server = fields.Boolean('Meli server')