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
from odoo.exceptions import AccessError, ValidationError
from odoo.tools.safe_eval import safe_eval
from .exception import SyncError


def create_record(self, res_id, vals, obj_sync=False):
    """
    Function to extend the create
    :param self:
    :param res_id: record
    :param vals: values
    :param obj_sync: object of synchronization
    :return:
    """
    # si res_id es válido significa que es en tiempo real
    if res_id:
        try:
            if self.env.context.get('sync', False):
                return res_id
            else:
                # buscamos los campos que solo estan configurados
                # son los que se van a registrar para enviar
                intersept = set(obj_sync.sudo().mapped('models_ids.name_f.name')) \
                    .intersection(set(vals))
                values = dict()
                # dejamos en values solo los vals que estan en la configuración
                for i in intersept:
                    if i in vals.keys():
                        values.setdefault(i, False)
                        values[i] = vals[i]
                if values:
                    obj_sync.sudo().send_records_real_time(res_id, values)
                return res_id
        except Exception as e:
            raise SyncError(
                _('The following error occurred when contacting the '
                  'server. %s') % (e,))
    else:
        # si llegó aquí significa que es via cron
        if self.env.context.get('sync', False):
            # si viene sync en el contexto significa que viene desde
            # el sistema externo, no se puede marcar para sincronizar
            vals['x_sync_service_now'] = False
            vals['x_values_changed'] = ''
        else:
            list_val = []
            for key in vals.keys():
                if vals.get(key, False):
                    list_val.append(key)
            # buscamos los campos que solo estan configurados
            # son los que se van a registrar para enviar
            intersept = set(obj_sync.sudo().mapped('models_ids.name_f.name')) \
                .intersection(set(list_val))
            # si los campos que vienen no estan en configuracion
            # insertamos el registro pero no marcamos nada
            if not intersept:
                return vals
            vals['x_sync_service_now'] = True
            vals['x_values_changed'] = list(intersept)
        return vals


def write_record(self, vals, obj_sync=False, via=None):
    """
    Function to extend write
    :param self:
    :param vals: vlas
    :param obj_sync: object of synchronization
    :param via: via (cron or real_time)
    :return:
    """
    # si res es válido significa que es en tiempo real
    if via == 'real_time':
        try:
            if self.env.context.get('sync', False):
                return vals
            else:
                # buscamos los campos que solo estan configurados
                # son los que se van a registrar para enviar
                intersept = set(obj_sync.sudo().mapped('models_ids.name_f.name')) \
                    .intersection(set(vals))
                values = dict()
                # dejamos en values solo los vals que estan en la configuración
                for i in intersept:
                    if i in vals.keys():
                        values.setdefault(i, False)
                        values[i] = vals[i]
                if values:
                    obj_sync.sudo().send_records_real_time(self, values)
                return vals
        except Exception as e:
            raise SyncError(
                _('The following error occurred when contacting the '
                  'server. %s') % (e,))

    elif via == 'cron':
        # si llegó aquí significa que es vía cron
        if self.env.context.get('error', False) or self.env.context.get('merge', False):
            # si viene error en contexto significa que dio error
            # al enviar la confirmación del ws, por tanto se deja
            # marcado para el proximo intento
            vals['x_sync_service_now'] = True
        else:
            if self.env.context.get('sync', False):
                # si viene sync en el contexto significa que viene desde
                # el sistema externo, no se puede marcar para sincronizar
                vals['x_sync_service_now'] = False
                vals['x_values_changed'] = ''
            else:
                list_val = []
                for rec in self:
                    values = rec.x_values_changed
                    list_val = []
                    if values and values != '':
                        list_val += safe_eval(values)
                for key in vals.keys():
                    if key not in list_val:
                        list_val.append(key)
                # buscamos los campos que solo estan configurados
                # son los que se van a registrar para enviar
                intersept = set(
                    obj_sync.sudo().mapped('models_ids.name_f.name')) \
                    .intersection(set(list_val))
                # si los campos que vienen no estan en configuracion
                # insertamos el registro pero no marcamos nada
                if not intersept:
                    return vals
                vals['x_sync_service_now'] = True
                vals['x_values_changed'] = list_val
        return vals


def unlink_record(self, obj_sync=False, via=None):
    """
    Function to extend the unlink
    :param self:
    :param obj_sync: object of synchronization
    :param via: via (cron or real_time)
    :return:
    """
    # si res es válido significa que es en tiempo real
    if via == 'real_time':
        try:
            if not self.env.context.get('sync', False):
                obj_sync.sudo().send_unlinked_records_real_time(self)
        except Exception as e:
            raise SyncError(
                _('The following error occurred when contacting the '
                  'server. %s') % (e,))

    elif via == 'cron':
        if self.env.context.get('sync', False):
            return True
        else:
            # si llegó aquí significa que es vía cron
            model_unlinked = obj_sync.sudo().model_unlinked
            # se busca si en el objeto de confiuración está
            # establecido el modelo para los registros eliminados
            if model_unlinked and self.x_sys_id:
                obj_unlinked = self.env[model_unlinked.model]
                model_id = self.env['ir.model'].search(
                    [('model', '=', self._name)],
                    limit=1).id,
                values = {
                    'name': self.name,
                    'external_id': self.x_sys_id,
                    'odoo_id': self.id,
                    'model_id': model_id,
                    'description': self._description
                }
                # se crea un registro en este modelo
                obj_unlinked.sudo().create(values)
    return True


class BaseModelExtend(models.AbstractModel):
    _name = 'basemodel.extend'
    _description = "Base model"

    def _register_hook(self):
        origin_create = models.AbstractModel.create
        origin_write = models.AbstractModel.write
        origin_unlink = models.AbstractModel.unlink
        models.AbstractModel.create_record = create_record
        models.AbstractModel.write_record = write_record
        models.AbstractModel.unlink_record = unlink_record

        @api.returns('self', lambda value: value.id)
        def copy(self, default=None):
            self.ensure_one()
            vals = self.with_context(active_test=False).copy_data(default)[0]
            x_sys_id = vals.get('x_sys_id', False)
            if x_sys_id:
                vals.pop('x_sys_id', False)
            # To avoid to create a translation in the lang of the user, copy_translation will do it
            new = self.with_context(lang=None).create(vals).with_env(self.env)
            self.with_context(from_copy_translation=True).copy_translations(new,
                                                                            excluded=default or ())
            return new

        @api.model
        @api.returns('self', lambda value: value.id)
        def create(self, vals):
            model = self._name
            obj_sync = False

            if self.env.registry.get('synchro.obj', False):
                try:
                    obj_sync = self.env['synchro.obj'].sudo().search(
                        [('direction', 'in', ['odoo2ext', 'bidirectional'])]). \
                        filtered(lambda x: x.odoo_model.model == model)
                except Exception as e:
                    if isinstance(e, SyncError):
                        raise AccessError(e)
                    else:
                        raise ValidationError(e)
            if not obj_sync:
                # si el modelo no esta en configuracion retornamos el original
                return origin_create(self, vals)
            if obj_sync.synchro_mode == 'via_cron':
                # si el modo de sincronizacion es 'via cron' nos vamos por
                # esta via
                vals = create_record(self, False, vals, obj_sync=obj_sync)
                return origin_create(self, vals)
            elif obj_sync.synchro_mode == 'real_time':
                # si el modo de sincronizacion es 'en tiempo real' nos vamos
                # por esta via
                res_id = origin_create(self, vals)
                return create_record(self, res_id, vals, obj_sync=obj_sync)
            return origin_create(self, vals)

        def write(self, vals):
            if self._name == 'ir.module.module':
                return origin_write(self, vals)
            model = self._name
            obj_sync = False
            if self.env.registry.get('synchro.obj', False):
                try:
                    # se busca si el modelo en cuestión está en la configuracion
                    obj_sync = self.env['synchro.obj'].sudo().search(
                        [('direction', 'in', ['odoo2ext', 'bidirectional'])]). \
                        filtered(lambda x: x.odoo_model.model == model)
                except Exception as e:
                    if isinstance(e, SyncError):
                        raise AccessError(e)
                    else:
                        raise ValidationError(e)
            if not obj_sync:
                # si el modelo no esta en configuracion retornamos el original
                return origin_write(self, vals)
            if obj_sync.synchro_mode == 'via_cron':
                # si el modo de sincronizacion es 'via cron' nos vamos por
                # esta via
                vals = write_record(self, vals, obj_sync=obj_sync, via='cron')
                return origin_write(self, vals)
            elif obj_sync.synchro_mode == 'real_time':
                # si el modo de sincronizacion es 'en tiempo real' nos vamos
                # por esta via
                vals = write_record(self, vals, obj_sync=obj_sync, via='real_time')
                return origin_write(self, vals)
            return origin_write(self, vals)

        def unlink(self):
            model = self._name
            # se busca si el modelo en cuestión está en la configuracion
            obj_sync = False
            if self.env.registry.get('synchro.obj', False):
                try:
                    obj_sync = self.env['synchro.obj'].sudo().search(
                        [('direction', 'in', ['odoo2ext', 'bidirectional'])]). \
                        filtered(lambda x: x.odoo_model.model == model)
                except Exception as e:
                    if isinstance(e, SyncError):
                        raise AccessError(e)
                    else:
                        raise ValidationError(e)
            if not obj_sync:
                # si el modelo no esta en configuracion retornamos el original
                return origin_unlink(self)
            if obj_sync.synchro_mode == 'via_cron':
                # si el modo de sincronizacion es 'via cron' nos vamos por
                # esta via
                unlink_record(self, obj_sync=obj_sync, via='cron')
                return origin_unlink(self)
            elif obj_sync.synchro_mode == 'real_time':
                # si el modo de sincronizacion es 'en tiempo real' nos vamos
                # por esta via
                unlink_record(self, obj_sync=obj_sync, via='real_time')
                return origin_unlink(self)
            return origin_unlink(self)

        models.AbstractModel.create = create
        models.AbstractModel.write = write
        models.AbstractModel.unlink = unlink
        models.AbstractModel.copy = copy
        return super(BaseModelExtend, self)._register_hook()
