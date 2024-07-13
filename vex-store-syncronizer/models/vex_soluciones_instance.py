from odoo import models, fields, api

class VexSolucionesInstance(models.Model):
    _name = "vex.instance"

    name = fields.Char('Name')

    status = fields.Selection([
        ('introduction', 'INTRODUCTION'),
        ('initial_settings', 'INITIAL SETTINGS'),
        ('keys', 'KEYS'),
        ('settings', 'SETTINGS')
    ], string='Status', default="introduction")

    instance_status = fields.Selection([
        ('inactive', 'Inactive'),
        ('activo', 'Activo')
    ], string='Instance status', default="activo")

    image = fields.Image('Image') # , max_width=30, max_height=30

    store = fields.Selection([], string="Store")

    state_order = {
        'introduction': 0,
        'initial_settings': 1,
        'keys': 2,
        'settings': 3
    }

    @api.model
    def get_status(self, id):
        status = self.env['vex.instance'].search([('id', '=', id)]).status
        status_value = self.state_order.get(status, -1)
        return status_value

    def back_instance(self):
        current_position = self.state_order.get(self.status, -1)
        if current_position > 0:
            previous_state = next(key for key, value in self.state_order.items() if value == current_position - 1)
            self.status = previous_state

    def next_instance(self):
        current_position = self.state_order.get(self.status, -1)
        if current_position < len(self.state_order) - 1:
            next_state = next(key for key, value in self.state_order.items() if value == current_position + 1)
            self.status = next_state