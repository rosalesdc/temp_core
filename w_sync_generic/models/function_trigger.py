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

from odoo import fields, models, api, _
from odoo.tools.safe_eval import safe_eval as eval


class FunctionTrigger(models.Model):
    _name = 'function.trigger'
    _description = "Function Triggers"
    _order = 'sequence'

    active = fields.Boolean(
        default=True
    )
    sequence = fields.Integer(
        default=1
    )
    name = fields.Char(
        required=True
    )
    python_code = fields.Text()
    key = fields.Char()
    url_api = fields.Char(
        compute="_compute_api"
    )

    @api.onchange('key')
    def _compute_api(self):
        for rec in self:
            if rec.key:
                params = self.env['ir.config_parameter'].sudo()
                base_web = params.get_param('web.base.url')
                rec.url_api = '%s/trigger/%s' % (base_web, rec.key)

    @api.model
    def _get_eval_context(self, data):
        cr = self.env.cr
        env = self.env
        eval_context = {
            'env': env,
            'cr': cr,
            'date': fields.Date,
            'data': data
        }
        return eval_context

    def run_code(self, data):
        generate_logs = self.env['ir.config_parameter'].sudo().get_param(
            'w_sync.generate_logs', default=False)
        ip = self.env.context.get('ip', '')
        try:
            eval_context = self._get_eval_context(data=data)
            res = eval(self.python_code, eval_context, mode='exec', nocopy=True)
            if generate_logs:
                self.env['history.synchro.log'].sudo().create(
                    {
                        'trace': 'external-odoo',
                        'name': _('Trigger %s') % self.name,
                        'action_type': 'trigger',
                        'date_sync': fields.Datetime.now(),
                        'date_write': fields.Datetime.now(),
                        'state': 'success',
                        'values_from_origin': str(data),
                        'ip': ip
                    }
                )
                self.env.cr.commit()
            return res
        except Exception as e:
            self.env['history.synchro.log'].sudo().create(
                {
                    'trace': 'external-odoo',
                    'name': _('Trigger %s') % self.name,
                    'action_type': 'trigger',
                    'date_sync': fields.Datetime.now(),
                    'date_write': fields.Datetime.now(),
                    'state': 'failed',
                    'values_from_origin': str(data),
                    'error_message': str(e),
                    'ip': ip
                }
            )
            self.env.cr.commit()
            raise e
