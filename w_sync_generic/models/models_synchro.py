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
FIELD_TYPES = [(key, key) for key in sorted(fields.Field.by_type)]


class FieldsSynchro(models.Model):
    _name = 'fields.synchro'
    _description = "Fields synchro"
    _order = 'sequence'

    sequence = fields.Integer(
        default=1
    )
    name = fields.Char(
        required=True
    )
    code = fields.Char(
        required=True
    )
    model_id = fields.Many2one(
        'models.synchro'
    )
    type = fields.Selection(
        selection=FIELD_TYPES,
        string='Field Type',
        required=True
    )


class ModelsSynchro(models.Model):
    _name = 'models.synchro'
    _description = "Models synchro"
    _order = 'sequence'

    sequence = fields.Integer(
        default=1000,
    )
    name = fields.Char(
        required=True
    )
    code = fields.Char(
        required=True
    )
    fields_ids = fields.One2many(
        'fields.synchro',
        'model_id'
    )
