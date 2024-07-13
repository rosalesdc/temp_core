# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2020 Wedoo - http://www.wedoo.tech/
# All Rights Reserved.
#
# Developer(s): Randy La Rosa Alvarez
#               (rra@wedoo.tech)
#
########################################################################
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
########################################################################

from odoo import fields, models
import random
import string


def _default_unique_key(size, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    api_key = fields.Char(
        string='API Secret key'
    )
    generate_logs = fields.Boolean(
        string="Generate Logs"
    )

    def generate_secret_key(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'w_sync.api_key', _default_unique_key(32))

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['api_key'] = self.env['ir.config_parameter'].sudo().get_param(
            'w_sync.api_key', default='')
        res['generate_logs'] = self.env['ir.config_parameter'].sudo().get_param(
            'w_sync.generate_logs', default=False)
        return res

    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'w_sync.api_key', self.api_key)
        self.env['ir.config_parameter'].sudo().set_param(
            'w_sync.generate_logs', self.generate_logs)
        super(ResConfigSettings, self).set_values()
