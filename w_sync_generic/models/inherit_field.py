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

from odoo import fields, models, api, _, registry
from odoo.exceptions import AccessError


def monkey_patch(cls):
    """ Return a method decorator to monkey-patch the given class. """
    def decorate(func):
        name = func.__name__
        func.super = getattr(cls, name, None)
        setattr(cls, name, func)
        return func
    return decorate


def first(records):
    """ Return the first record in ``records``, with the same prefetching. """
    return next(iter(records)) if len(records) > 1 else records


@monkey_patch(fields.Field)
def _compute_related(self, records):
    """ Compute the related field ``self`` on ``records``. """
    model = records._name
    update_related = False

    objects = records.env['synchro.obj'].sudo().search([('synchro_mode', '=', 'via_cron')]).filtered(lambda x: x.sudo().odoo_model.model == model)
    if objects and objects.models_ids.filtered(lambda x: x.sudo().name_f.name == self.name):
        update_related = True
    values = list(records)
    for name in self.related.split('.')[:-1]:
        try:
            values = [first(value[name]) for value in values]
        except AccessError as e:
            description = records.env['ir.model']._get(records._name).name
            raise AccessError(
                _("%(previous_message)s\n\nImplicitly accessed through '%(document_kind)s' (%(document_model)s).") % {
                    'previous_message': e.args[0],
                    'document_kind': description,
                    'document_model': records._name,
                }
            )
    # assign final values to records
    for record, value in zip(records, values):
        if update_related:
            list_values = eval(record.x_values_changed or '[]')
            list_values.append(self.name)
            record.with_context(check_move_validity=False).write({
                'x_values_changed': list_values,
                'x_sync_service_now': True
            })
        record[self.name] = self._process_related(value[self.related_field.name])
