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


class ModelRecordsUnlinked(models.Model):
    _name = 'model.records.unlinked'
    _description = 'Model Records Unlinked'

    name = fields.Char(
        'Name',
        help='Name of the record.'
    )
    external_id = fields.Char(
        string='External Id'
    )
    odoo_id = fields.Char(
        string='Odoo Id'
    )
    model_id = fields.Many2one(
        'ir.model',
        string="Model"
    )
    description = fields.Char(
        string='Description'
    )


