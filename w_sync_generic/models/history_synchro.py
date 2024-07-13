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


class HistorySynchro(models.Model):
    """Model to manage synchronization logs."""

    _name = 'history.synchro.log'
    _description = "History synchro"

    trace = fields.Selection(
        [
            ('external-odoo', 'External-Odoo'),
            ('odoo-external', 'Odoo-External')
        ],
        help="Field to know the traceability of synchronization."
    )
    name = fields.Char(
        help="Field to know the model of the changes."
    )
    action_type = fields.Selection(
        [
            ('create', 'Create'),
            ('write', 'Write'),
            ('unlink', 'Unlink'),
            ('trigger', 'Trigger'),
        ],
        help="Field to know the operation in the synchronization."
    )
    values_from_origin = fields.Char(
        help="Values received from the origin in the synchronization."
    )
    values_to_destiny = fields.Char(
        help="Values sents to the destiny in the synchronization."
    )
    date_write = fields.Datetime(
        help="Date it was modificated the record."
    )
    date_sync = fields.Datetime(
        help="Date it was realizated the synchronization."
    )
    external_id = fields.Char(
        help="Field to know the ID record of External system."
    )
    odoo_id = fields.Char(
        help="Field to know the ID record of Odoo."
    )
    state = fields.Selection(
        [('failed', 'Failed'), ('success', 'Success')]
    )
    error_message = fields.Char(
        help="Message of error if the syncronization was failed."
    )
    title = fields.Char(
        help="Name of the record that has been syncronized."
    )
    model = fields.Char(
        help="Name of model associate to log."
    )
    ip = fields.Char(
        string="IP"
    )

    def name_get(self):
        res = []
        for rec in self:
            action_type = dict(self.fields_get('action_type')
                               ['action_type']['selection'])[rec.action_type]
            name = '%s %s %s' % (action_type, rec.model or '',
                                 rec.title or '')
            res.append((rec.id, name))
        return res
