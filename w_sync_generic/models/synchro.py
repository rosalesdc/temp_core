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

import odoo
from odoo import fields, models, api, _
from odoo.tests.common import Form
from odoo.exceptions import ValidationError, UserError
from odoo.tools.safe_eval import safe_eval as eval
import logging
import requests
import json
from requests.auth import HTTPBasicAuth
from odoo.osv import expression
_logger = logging.getLogger(__name__)

FIELD_TYPES = [(key, key) for key in sorted(fields.Field.by_type)]


class WebServiceApiRest(models.Model):
    _name = 'web.service.api.rest'
    _description = 'Web Service Api Rest'

    activ = fields.Boolean(
        string="Active",
        default=True
    )
    name = fields.Char(
        string='Url'
    )
    action = fields.Selection(
        [
            ('insert', 'CREATE'),
            ('update', 'WRITE'),
            ('delete', 'UNLINK')
        ],
        string='Action'
    )
    method = fields.Selection(
        [
            ('get', 'GET'),
            ('post', 'POST'),
            ('put', 'PUT'),
            ('del', 'DELETE')
        ],
        string='Method'
    )
    description = fields.Char(
        string='Description'
    )
    obj_sync_id = fields.Many2one('synchro.obj')
    context = fields.Char(string="Context", default='{}')


class WebServiceHeaderLine(models.Model):
    _name = 'web.service.header.line'
    _description = "Web Service Header Lines"

    name = fields.Char(string='Key')
    value = fields.Char(string='Value')
    web_service_id = fields.Many2one('web.service.url')


class WebServiceUrl(models.Model):
    _name = 'web.service.url'
    _description = "Web Service"

    active = fields.Boolean(
        default=True
    )
    name = fields.Char(
        required=True
    )
    url = fields.Char(
        help="URL Web Service",
        required=True
    )
    url_send = fields.Char(
        string="URL to Send"
    )
    need_confirmation = fields.Boolean(
        string="Need confirmation",
        help="Check if the WS need a return of confirmation"
    )
    url_confirmation = fields.Char(
        string="URL Confirmation"
    )
    need_authentication = fields.Boolean(
        string="Need authentication",
        help="Check if the WS need authentication"
    )
    authentication_mode = fields.Selection(
        selection=[
            ('api_key', 'Api Key'),
            ('user_pass', 'User and Password')
        ],
        default='api_key',
        string='Authentication Mode'
    )
    header_line_ids = fields.One2many(
        'web.service.header.line',
        'web_service_id',
        string="Headers"
    )
    api_key = fields.Char()
    username = fields.Char()
    password = fields.Char()

    def get_headers(self, function=''):
        """
        Function to build de headers
        :param function:
        :return: dict(): headers
        """
        header = dict()
        for rec in self:
            for line in rec.header_line_ids:
                header.setdefault(line.name, line.value)
                header[line.name] = line.value
        return header

    def get_data(self, data={}):
        """
        Function to build the data
        :param data:
        :return: json(): data
        """
        return json.dumps(data)

    def get_payload(self, payload={}):
        """
        Function to build a paylod
        :param payload:
        :return: json(): payload
        """
        return json.dumps(payload)

    def get_url(self, param={}):
        """
        Function to build the url
        :param param:
        :return: string(): url
        """
        return self.url

    def get_url_confirmation(self, param={}):
        """
        Function to build the auth url
        :param param:
        :return: string(): url
        """
        return self.url_confirmation

    def get_url_send(self, param={}):
        """
        Function to build the url to send
        :param param:
        :return: string(): url
        """
        return self.url_send

    def get_auth(self):
        """
        Function to auth
        :return: json(): response
        """
        if self.need_authentication:
            if self.authentication_mode == 'api_key':
                return HTTPBasicAuth('apikey', self.api_key)
            else:
                return HTTPBasicAuth(self.username, self.password)
        else:
            return None

    def receive_data(self, data={}):
        """
        Function to receive data
        :param data: dict(): data with params
        :return: json(): response
        """
        try:
            url = self.get_url()
            headers = self.get_headers(function='receive')
            auth = self.get_auth()
            payload = self.get_payload(data)
            data = self.get_data(data)
            response = requests.post(
                url,
                headers=headers,
                auth=auth,
                json=payload,
                data=data
            )
            if response.ok:
                return response.json()
        except Exception as e:
            raise ValidationError(e)

    def send_confirmation(self, data):
        """
        Function to send confirmation
        :param data: dict(): data with record to confirm
        :return: json(): response
        """
        try:
            url = self.get_url_confirmation()
            headers = self.get_headers(function='confirmation')
            auth = self.get_auth()
            payload = self.get_payload(data)
            data = self.get_data(data)
            response = requests.post(
                url,
                headers=headers,
                auth=auth,
                json=payload,
                data=data
            )
            return response.json()
        except Exception as e:
            raise ValidationError(e)

    def send_data(self, data):
        """
        Function to send data
        :param data: dict(): data to send
        :return: json(): response
        """
        try:
            url = self.get_url_send()
            if not url:
                msg = _('The URL to send is not defined.')
                raise ValidationError(msg)
            else:
                headers = self.get_headers(function='send')
                auth = self.get_auth()
                payload = self.get_payload(data)
                data = self.get_data(data)
                response = requests.post(
                    url,
                    headers=headers,
                    auth=auth,
                    json=payload,
                    data=data
                )
                if response.status_code in [404]:
                    raise ValidationError(response.text)
                return response.json()

        except Exception as e:
            return {
                'status': 'error',
                'error_message': e
            }


class ModelExternal(models.Model):
    _name = 'model.external'
    _description = "Model external"
    _order = 'sequence'

    activo = fields.Boolean(
        string='Active',
        default=True
    )
    sequence = fields.Integer(
        default=1
    )
    name = fields.Char()
    name_f = fields.Many2one(
        'ir.model.fields',
        string="Odoo Field",
        domain="[('model_id', '=', parent.odoo_model)]"
    )
    type = fields.Selection(
        related="name_f.ttype"
    )
    operator = fields.Selection(
        [('equal', '='), ('not_equal', '!=')],
        default='equal'
    )
    external_field = fields.Many2one(
        'fields.synchro',
        domain="[('model_id', '=', parent.external_model)]"
    )
    reference_field = fields.Char(
        help="Reference field to relational fields",
    )
    syncro_id = fields.Many2one(
        'synchro.obj',
    )
    details = fields.Text(
        string='Details',
        help='Details of errors found'
    )


class SynchroObj(models.Model):
    _name = 'synchro.obj'
    _description = "synchro obj"
    _order = 'priority ASC'

    active = fields.Boolean(
        default=True
    )
    name = fields.Char(
    )
    priority = fields.Integer(
    )
    odoo_model = fields.Many2one(
        'ir.model'
    )
    direction = fields.Selection(
        [
            ('odoo2ext', 'Odoo to External'),
            ('ext2odoo', 'External to Odoo'),
            ('bidirectional', 'Bidirectional')
        ],
        default='odoo2ext'
    )
    synchro_mode = fields.Selection(
        [
            ('via_cron', 'Via Cron'),
            ('real_time', 'Real Time')
        ],
        string="Synchro Mode",
        help="If Via Cron is selected, the synchronization will be "
             "executed by means of a planned action at the desired "
             "time, if Real Time is selected, the synchronization "
             "will be carried out in real time.",
        default='via_cron'
    )
    synchro_priority = fields.Selection(
        [
            ('odoo2ext', 'Odoo to External'),
            ('ext2odoo', 'External to Odoo')
        ],
        string="Synchro Priority",
        help="Set synchronization priority"
    )
    reference_field_odoo = fields.Many2one(
        'ir.model.fields',
        domain="[('model_id', '=', odoo_model)]"
    )
    external_model = fields.Many2one(
        'models.synchro'
    )
    external_model_name = fields.Char(
        related='external_model.code'
    )
    reference_field_ext = fields.Many2one(
        'fields.synchro',
        domain="[('model_id', '=', external_model)]",
        required=True
    )
    ws_url_id = fields.Many2one(
        'web.service.url',
        string="WS to receive",
        help="Select the WS to conect with External system."
    )
    models_ids = fields.One2many(
        'model.external',
        'syncro_id',
    )
    description = fields.Text(
    )
    session_id = fields.Integer(
    )
    model_unlinked = fields.Many2one(
        'ir.model',
    )
    domain = fields.Char(
        help="Optional domain filtering of the destination data, "
             "as a Python expression",
        default="[]"
    )
    limit = fields.Integer(
        string="Limit",
        default=15
    )
    api_ids = fields.One2many(
        'web.service.api.rest',
        'obj_sync_id',
        string="Api",
        store=True
    )
    date_last_synchro = fields.Datetime(
        string="Datetime last synchro"
    )
    send_type = fields.Selection(
        [
            ('changed_values', 'Only modified values'),
            ('all_values', 'All values'),
        ],
        default='changed_values',
        string="Shipping type",
        help="If Only modified values is setted, only the data of the fields "
             "that were modified will be sent, but if All values is setted, "
             "all the data of the configured fields will be sent"
    )
    code = fields.Text(string='Python Code', groups='base.group_system',
                       help="Write Python code that the action will execute.")

    @api.onchange('external_model', 'external_model.code', 'synchro_mode',
                  'direction')
    def _compute_api(self):
        for rec in self:
            if rec.synchro_mode == 'real_time' and rec.direction \
                    in ['ext2odoo', 'bidirectional']:
                rec.api_ids = False
                list_apis = []
                params = self.env['ir.config_parameter'].sudo()
                base_web = params.get_param('web.base.url')
                actions = [
                    ('insert', 'post', 'create',
                     _('Pass dict of values in data.')),
                    ('update', 'put', '<string: record_id>',
                     _('Pass dict of values in data.')),
                    ('delete', 'del', '<string: record_id>', ''),
                ]

                for action in actions:
                    code = rec.external_model.code
                    url = '%s/sync/%s' % (base_web, code)
                    if action[2]:
                        url = url + '/%s' % action[2]
                    vals = {
                        'action': action[0],
                        'method': action[1],
                        'name': url,
                        'description': action[3],
                        'obj_sync_id': rec.id
                    }
                    api = self.env['web.service.api.rest'].sudo().create(vals)
                    list_apis.append(api.id)
                rec.api_ids = list_apis
            else:
                rec.api_ids = False

    @api.onchange('odoo_model')
    def onchange_odoo_model(self):
        """
          Onchange to create a necesary fields in model to use.
        :return: void()
        """
        model_name = self.odoo_model.model
        ir_models = self.env['ir.model'].search(
            [('model', '=', model_name)])
        ir_models_fields = self.env['ir.model.fields']
        x_values_changed = {
            'name': 'x_values_changed',
            'field_description': _("Values changed"),
            'ttype': 'char',
            'state': 'manual'
        }
        x_sys_id = {
            'name': 'x_sys_id',
            'field_description': _("Id ext"),
            'ttype': 'char',
            'state': 'manual'
        }
        x_sync_service_now = {
            'name': 'x_sync_service_now',
            'field_description': _("Sync service now"),
            'ttype': 'boolean',
            'state': 'manual'
        }
        name = self.name
        ws_url_id = self.ws_url_id
        direction = self.direction
        synchro_mode = self.synchro_mode
        odoo_model = self.odoo_model
        external_model = self.external_model
        reference_field_ext = self.reference_field_ext
        send_type = self.send_type
        model_unlinked = self.model_unlinked

        if self.odoo_model:
            for ir_model in ir_models:
                if 'x_values_changed' not in ir_model.mapped('field_id.name'):
                    x_values_changed.update(
                        {
                            'model_id': ir_model.id
                        })
                    ir_models_fields.sudo().create(x_values_changed)
                if 'x_sys_id' not in ir_model.mapped('field_id.name'):
                    x_sys_id.update(
                        {
                            'model_id': ir_model.id
                        })
                    ir_models_fields.sudo().create(x_sys_id)
                if 'x_sync_service_now' not in ir_model.mapped('field_id.name'):
                    x_sync_service_now.update(
                        {
                            'model_id': ir_model.id
                        })
                    ir_models_fields.sudo().create(x_sync_service_now)

        self.name = name
        self.ws_url_id = ws_url_id
        self.direction = direction
        self.synchro_mode = synchro_mode
        self.odoo_model = odoo_model
        self.external_model = external_model
        self.reference_field_ext = reference_field_ext
        self.send_type = send_type
        self.model_unlinked = model_unlinked

    def run_synchro(self, objects_to_sync):
        """
        Function to execute the synchronization
        :return: void()
        """
        dom = ['|', ('x_sync_service_now', '=', True), ('x_sys_id', '=', False)]
        for obj_sync in objects_to_sync:
            limit = obj_sync.limit or 15
            if obj_sync.domain:
                domain = expression.AND([dom, eval(obj_sync.domain)])
            else:
                domain = dom
            if obj_sync.direction == 'bidirectional':
                if obj_sync.synchro_priority == 'odoo2ext':
                    # enviar registros modificados para externo
                    records_sync = self.env[obj_sync.odoo_model.model].search(
                        domain, limit=limit)
                    for record in records_sync:
                        obj_sync.send_records_via_cron(record)
                    # enviar registros eliminados para externo si está definido
                    if obj_sync.model_unlinked:
                        obj_sync.send_unlinked_records_via_cron()
                    # recibir registros desde externo
                    obj_sync.receive_records_via_cron()
                else:
                    # recibir registros desde externo
                    self.with_context(match=True).receive_records_via_cron()
                    # enviar registros modificados para externo
                    records_sync = self.env[obj_sync.odoo_model.model].search(
                        domain, limit=limit)
                    for record in records_sync:
                        obj_sync.send_records_via_cron(record)
                    # enviar registros eliminados para externo
                    if obj_sync.model_unlinked:
                        obj_sync.send_unlinked_records_via_cron()
            elif obj_sync.direction == 'odoo2ext':
                # enviar registros modificados para externo
                records_sync = self.env[obj_sync.odoo_model.model].search(
                    domain, limit=limit)
                for record in records_sync:
                    obj_sync.send_records_via_cron(record)
                # enviar registros eliminados para externo si está definido
                if obj_sync.model_unlinked:
                    obj_sync.send_unlinked_records_via_cron()
            else:
                # recibir registros desde externo
                self.receive_records_via_cron()

            objects_to_sync.write(
                {
                    'date_last_synchro': fields.Datetime.now()
                }
            )

    def run_via_button(self):
        """
        Function to execute the synchronization procedure via button
        :return: void()
        """
        for objects_to_sync in self:
            self.run_synchro(objects_to_sync)

    def run_via_cron(self):
        """
        Function to execute the synchronization procedure via cron
        :return: void()
        """
        objects_to_sync = self.env['synchro.obj'].sudo().search(
            [('synchro_mode', '=', 'via_cron')])
        self.run_synchro(objects_to_sync)

    def receive_records_via_cron(self):
        """
        Function to receive the records from the external
        :return: sync response
        """
        generate_logs = self.env['ir.config_parameter'].sudo().get_param(
            'w_sync.generate_logs', default=False)
        # primero elaboramos un data con el límite de la cantidad de registros
        # que queremos obtener
        data = {
            'limit': self.limit or 15
        }
        # enviamos ese data al ws
        response = self.sync_to_receive(data)
        status = response.get('status', False)
        records_to_insert = response.get('content', [])
        # si dio error para ese modelo no hacemos nada
        if status in ['error', 'failed']:
            return False
        # si no dio error obtenemos todos los registros
        content = []
        for record in records_to_insert:
            values = record.get('values', {})
            fields_received = list(values.keys())
            field_in_odoo = self.reference_field_odoo.name
            field_in_ext = self.reference_field_ext.code
            external_val = ''
            for f_r in fields_received:
                if f_r == field_in_ext:
                    external_val = values[f_r]
                    break
            vals = dict()
            vals.setdefault(field_in_ext, external_val)
            action = record.get('action', False)
            Model = self.env[self.odoo_model.model].sudo()
            # recorremos cada registro
            # si el action es delete, significa que este record fue eliminado
            # en el externo, necesitamos eliminarlo en odoo
            if action in ['delete']:
                # si field_in_odoo es True, significa que en los values
                # viene el campo referencia para este modelo
                # por lo que buscamos el registro por el external_val que es
                # el valor que viene.
                if field_in_odoo:
                    domain = [(field_in_odoo, '=', external_val)]
                    obj = Model.search(domain, limit=1)
                    if obj:
                        # existe el registro en odoo
                        if generate_logs:
                            self.env['history.synchro.log'].sudo().create(
                                {
                                    'trace': 'external-odoo',
                                    'name': _('Unlink %s') % self.odoo_model.name,
                                    'title': obj.name,
                                    'action_type': 'unlink',
                                    'date_sync': fields.Datetime.now(),
                                    'date_write': fields.Datetime.now(),
                                    'state': 'success',
                                    'odoo_id': obj.id,
                                    'external_id': external_val,
                                    'model': self.odoo_model.name
                                }
                            )
                        self.env.cr.commit()
                        content.append(
                            {
                                'status': 'success',
                                'error_message': False,
                                'external_id': external_val
                            }
                        )
                        ctx = self.env.context.copy()
                        ctx.update({'sync': True})
                        # le pasamos por contexto sync=True para que el metodo unlink
                        # no lo pase para el modelo de registros eliminados
                        obj.with_context(ctx).unlink()
                    else:
                        if generate_logs:
                            self.env['history.synchro.log'].sudo().create(
                                {
                                    'trace': 'external-odoo',
                                    'name': _('Unlink %s') % self.odoo_model.name,
                                    'title': _('Unknown'),
                                    'action_type': 'unlink',
                                    'date_sync': fields.Datetime.now(),
                                    'date_write': fields.Datetime.now(),
                                    'state': 'failed',
                                    'odoo_id': False,
                                    'external_id': external_val,
                                    'model': self.odoo_model.name
                                }
                            )
                        self.env.cr.commit()
                        content.append(
                            {
                                'status': 'failed',
                                'error_message': _('The record not exist in '
                                                   'Odoo.'),
                                'external_id': external_val
                            }
                        )

            # si llego hasta aqui es porque la accion debe ser inser_update
            values_updated = dict()
            # obtenemos los campos que estan en configuracion
            fields_in_conf = self.sudo().mapped(
                'models_ids.external_field.code')
            for field in fields_in_conf:
                if field in values.keys():
                    values_updated.setdefault(field, False)
                    values_updated[field] = values[field]
            try:
                # pasamos los values para obtener los vals destiny
                vals_origin, vals_destiny = self.sudo().convert_values_ext_odoo(
                values_updated)
            except Exception as e:
                content.append(
                    {
                        'status': 'failed',
                        'error_message': e,
                        'external_id': external_val
                    }
                )
                continue

            ctx = self.env.context.copy()
            # actualizamos contexto con sync=True porque los registros
            # que creamos o actualizamos vienen desde el sistema externo
            # por tanto no se pueden marcar como modificados en odoo
            ctx.update({'sync': True})
            try:
                v_destiny = vals_destiny.copy()
                # si odoo_id tiene valos significa que el registro existía en odoo
                # y que los que vamos a hacer es un update
                mod_rec = Model
                exist = True
                if field_in_odoo:
                    domain = [(field_in_odoo, '=', external_val)]
                    mod_rec |= Model.search(domain, limit=1)
                if not mod_rec:
                    exist = False
                    mod_rec |= Model.with_context(
                        ctx).sudo().create(vals_destiny)

                # bandera usada para cuando se va a sincronizar con prioridad
                # odoo, si lo campos que vienen del externo son los mismos
                # que están para enviar desde Odoo, no insertamos nada.
                flag_no_vals_destiny = False

                # si tiene values_changed es que ya existe y tiene valores
                # a sincronizar
                if mod_rec.x_values_changed:
                    # el match en el contexto es utilizado para la prioridad
                    if self.env.context.get('match', False):
                        values_changed = eval(mod_rec.x_values_changed)
                        for value in values_changed:
                            if value in vals_destiny.keys():
                                values_changed.remove(value)
                        if values_changed:
                            vals_destiny.update({
                                'x_values_changed': values_changed
                            })
                            # TODO: revisar contexto
                            mod_rec.with_context(merge=True).write(vals_destiny)
                        else:
                            mod_rec.with_context(ctx).write(vals_destiny)
                    else:
                        values_changed = eval(mod_rec.x_values_changed)
                        for value in vals_destiny.keys():
                            if value in values_changed:
                                vals_destiny.remove(value)
                        if vals_destiny:
                            mod_rec.with_context(merge=True).write(vals_destiny)
                        else:
                            flag_no_vals_destiny = True
                else:
                    mod_rec.with_context(ctx).write(vals_destiny)
                if exist:
                    if not flag_no_vals_destiny:
                        if generate_logs:
                            self.env['history.synchro.log'].sudo().create(
                                {
                                    'trace': 'external-odoo',
                                    'name': _('Write %s') % self.odoo_model.name,
                                    'title': mod_rec.name,
                                    'action_type': 'write',
                                    'date_sync': fields.Datetime.now(),
                                    'date_write': fields.Datetime.now(),
                                    'state': 'success',
                                    'odoo_id': mod_rec.id,
                                    'external_id': external_val,
                                    'values_from_origin': str(
                                        values_updated),
                                    'values_to_destiny': str(v_destiny),
                                    'model': self.odoo_model.name
                                }
                            )
                else:
                    if generate_logs:
                        self.env['history.synchro.log'].sudo().create(
                            {
                                'trace': 'external-odoo',
                                'name': _('Create %s') % self.odoo_model.name,
                                'title': mod_rec.name,
                                'action_type': 'create',
                                'date_sync': fields.Datetime.now(),
                                'date_write': fields.Datetime.now(),
                                'state': 'success',
                                'odoo_id': mod_rec.id,
                                'external_id': external_val,
                                'values_from_origin': str(
                                    values_updated),
                                'values_to_destiny': str(v_destiny),
                                'model': self.odoo_model.name
                            }
                        )
                        self.run_code(mod_rec)
                self.env.cr.commit()
                content.append(
                    {
                        'status': 'success',
                        'error_message': False,
                        'external_id': external_val,
                    }
                )
            except Exception as e:
                content.append(
                    {
                        'status': 'failed',
                        'error_message': str(e),
                        'external_id': external_val,
                    }
                )
                domain = [(field_in_odoo, '=', external_val)]
                odoo_id = Model.search(domain, limit=1)
                if odoo_id:
                    if generate_logs:
                        self.env['history.synchro.log'].sudo().create(
                            {
                                'trace': 'external-odoo',
                                'name': _('Write %s') % self.odoo_model.name,
                                'title': odoo_id.name,
                                'action_type': 'write',
                                'date_sync': fields.Datetime.now(),
                                'date_write': fields.Datetime.now(),
                                'state': 'failed',
                                'odoo_id': odoo_id.id,
                                'external_id': external_val,
                                'values_from_origin': str(
                                    values_updated),
                                'values_to_destiny': str(v_destiny),
                                'model': self.odoo_model.name
                            }
                        )
                else:
                    if generate_logs:
                        self.env['history.synchro.log'].sudo().create(
                            {
                                'trace': 'external-odoo',
                                'name': _('Create %s') % self.odoo_model.name,
                                'title': False,
                                'action_type': 'create',
                                'date_sync': fields.Datetime.now(),
                                'date_write': fields.Datetime.now(),
                                'state': 'failed',
                                'odoo_id': False,
                                'external_id': external_val,
                                'values_from_origin': str(values),
                                'model': self.odoo_model.name
                            }
                        )
        data = {
            'content': content
        }
        # elaboramos el data y enviamos las confirmaciones de cada registro
        response = self.sync_to_confirm(data)
        return response

    def send_records_via_cron(self, record):
        """
        Function to send records created or modified in odoo via cron
        :param record: record to send
        :return: void()
        """
        generate_logs = self.env['ir.config_parameter'].sudo().get_param(
            'w_sync.generate_logs', default=False)
        ctx = self.env.context.copy()
        ctx.update({'cron': True})
        field_in_odoo = self.sudo().reference_field_odoo.name
        external_val = record.read([field_in_odoo])[0].get(field_in_odoo,
                                                         False)
        # creamos el data con los values_destiny listos
        flag_continue = False
        if external_val:
            if self.send_type == 'changed_values':
                list_values = eval(record.x_values_changed or '[]')
                if not list_values:
                    flag_continue = True
                else:
                    values_changed = dict(zip(list_values, range(len(list_values))))
                    values_changed.update({'obj_id': record.id})
                    vals_origin, vals_destiny = self.with_context(
                        ctx).sudo().convert_values_odoo_ext(values_changed)
                    data = {
                        'action': 'update',
                        'values': vals_destiny,
                        'external_id': external_val,
                        'odoo_id': record.id
                    }
            else:
                fiels_to_sent = self.models_ids.filtered(
                    lambda x: x.activo).mapped('name_f.name')
                values_changed = dict(
                    zip(fiels_to_sent, range(len(fiels_to_sent))))
                values_changed.update({'obj_id': record.id})
                vals_origin, vals_destiny = self.with_context(
                    ctx).sudo().convert_values_odoo_ext(values_changed)
                data = {
                    'action': 'update',
                    'values': vals_destiny,
                    'external_id': external_val,
                    'odoo_id': record.id
                }

        else:
            fiels_to_sent = self.models_ids.filtered(
                lambda x: x.activo).mapped('name_f.name')
            values_changed = dict(zip(fiels_to_sent, range(len(fiels_to_sent))))
            values_changed.update({'obj_id': record.id})
            vals_origin, vals_destiny = self.with_context(
                ctx).sudo().convert_values_odoo_ext(values_changed)
            data = {
                'action': 'insert',
                'values': vals_destiny,
                'external_id': False,
                'odoo_id': record.id
            }
        if not flag_continue:
            # enviamos el data
            response = self.sudo().sync_to_send(data)
            status = response.get('status', False)
            error = response.get('error', False)
            error_message = response.get('error_message', '')
            # si el retorno del ws es error o failed creamos una
            # traza en el historial
            if status in ['error', 'failed'] or error:
                if generate_logs:
                    self.env['history.synchro.log'].sudo().create(
                        {
                            'trace': 'odoo-external',
                            'name': '%s %s' % (
                           _('Create') if not record.x_sys_id else _('Write'),
                            record._description),
                            'title': record.name,
                            'action_type': 'create' if not external_val else 'write',
                            'date_sync': fields.Datetime.now(),
                            'date_write': fields.Datetime.now(),
                            'state': 'failed',
                            'odoo_id': record.id,
                            'external_id': external_val if record.x_sys_id else False,
                            'values_from_origin': str(vals_origin),
                            'values_to_destiny': str(vals_destiny),
                            'model': self.odoo_model.name,
                            'error_message': error_message or error
                        }
                    )
                ctx.update({'error': True})
                record.with_context(ctx).sudo().write({})
            else:
                # en el response debe venir en el value el campo con el valor
                # del id_externo de este modelo
                # buscamos que el campo que viene coincide con el campo referencia
                # en la configuracion, y si es asi, buscamos su campo analogo en
                # odoo e insertamos el valor
                vals_up = dict()
                external_val = response.get('external_id', False)
                vals_up.setdefault(field_in_odoo, external_val)
                if external_val:
                    ctx.update({'sync': True})
                    record.with_context(ctx).sudo().write(vals_up)
                    if generate_logs:
                        self.env['history.synchro.log'].sudo().create(
                            {
                                'trace': 'odoo-external',
                                'name': '%s %s' % (
                                _('Create') if not record.x_sys_id else _('Write'),
                                record._description),
                                'title': record.name,
                                'action_type': 'create' if not record.x_sys_id else 'write',
                                'date_sync': fields.Datetime.now(),
                                'date_write': fields.Datetime.now(),
                                'state': 'success',
                                'odoo_id': record.id,
                                'external_id': external_val,
                                'values_from_origin': str(vals_origin),
                                'values_to_destiny': str(vals_destiny),
                                'model': self.odoo_model.name,
                            }
                        )
                else:
                    if generate_logs:
                        error_message = _('The Web Service not confirm the record sent.')
                        self.env['history.synchro.log'].sudo().create(
                            {
                                'trace': 'odoo-external',
                                'name': '%s %s' % (
                                    _('Create') if not record.x_sys_id else _('Write'),
                                    record._description),
                                'title': record.name,
                                'action_type': 'create' if not record.x_sys_id else 'write',
                                'date_sync': fields.Datetime.now(),
                                'date_write': fields.Datetime.now(),
                                'state': 'failed',
                                'odoo_id': record.id,
                                'external_id': external_val,
                                'values_from_origin': str(vals_origin),
                                'values_to_destiny': str(vals_destiny),
                                'model': self.odoo_model.name,
                                'error_message': error_message
                            }
                        )
                    ctx.update({'error': True})
                    record.with_context(ctx).sudo().write({})
            self.env.cr.commit()

    def send_unlinked_records_via_cron(self):
        """
        Function to delete deleted records via cron
        :return: void()
        """
        generate_logs = self.env['ir.config_parameter'].sudo().get_param(
            'w_sync.generate_logs', default=False)
        field_in_odoo = self.sudo().reference_field_odoo.name
        field_in_ext = self.sudo().reference_field_ext.code
        model_unlinked = self.sudo().model_unlinked
        # si hay modelo configurada para registros eliminados continuamos
        # si no, no hacemos nada
        if model_unlinked:
            domain_to_unlink = [
                ('model_id', '=', self.sudo().odoo_model.id)]
            # buscamos los registros eliminados
            records_to_unlink = self.env[model_unlinked.model].search(
                domain_to_unlink)
            for record in records_to_unlink:
                # por cada registro elaboramos el data a enviar
                external_val = record.read([field_in_odoo])[0].get(
                    field_in_odoo,
                    False)
                vals = dict()
                vals.setdefault(field_in_ext, external_val)
                data = {
                    'action': 'delete',
                    'external_id': external_val,
                    'odoo_id': record.odoo_id
                }
                # enviamos el data de eliminacion
                response = self.sudo().sync_to_send(data)
                status = response.get('status', False)
                error_message = response.get('error_message', '')
                # si el retorno del ws es error o failed creamos una
                # traza en el historial
                if status in ['error', 'failed']:
                    if generate_logs:
                        self.env['history.synchro.log'].sudo().create(
                            {
                                'trace': 'odoo-external',
                                'name': _('Unlink %s') % record._description,
                                'title': record.name,
                                'action_type': 'unlink',
                                'date_sync': fields.Datetime.now(),
                                'date_write': fields.Datetime.now(),
                                'state': 'failed',
                                'odoo_id': record.id,
                                'model': self.odoo_model.name,
                                'error_message': error_message
                            }
                        )
                if status == 'success':
                    if generate_logs:
                        # si el retorno de ws es success creamos la traza
                        # y eliminamos el registro del modelo de registros eliminados
                        self.env['history.synchro.log'].sudo().create(
                            {
                                'trace': 'odoo-external',
                                'name': _('Unlink %s') % record._description,
                                'title': record.name,
                                'action_type': 'unlink',
                                'date_sync': fields.Datetime.now(),
                                'date_write': fields.Datetime.now(),
                                'state': 'success',
                                'odoo_id': record.id,
                                'external_id': external_val,
                                'model': self.odoo_model.name,
                            }
                        )
                    record.sudo().unlink()
                self.env.cr.commit()

    def send_records_real_time(self, record, values):
        """
        Function to send records created or modified in odoo
        :param record: record to send
        :param values: dict(): modified fields
        :return: void()
        """
        generate_logs = self.env['ir.config_parameter'].sudo().get_param(
            'w_sync.generate_logs', default=False)
        # campos en los que se escribió en el registro
        list_values = list(values.keys())
        values_changed = dict(zip(list_values, range(len(list_values))))
        values_changed.update({'obj_id': record.id})
        # enviamos los values para obtener los values destino
        ctx = self.env.context.copy()
        ctx.update({'cron': True})
        # llamamos a la función que convierte los values a values_destiny
        vals_origin, vals_destiny = self.with_context(
            ctx).sudo().convert_values_odoo_ext(values_changed)
        field_in_odoo = self.sudo().reference_field_odoo.name
        external_val = record.read([field_in_odoo])[0].get(field_in_odoo,
                                                         False)
        # creamos el data con los values_destiny listos
        if external_val:
            data = {
                'action': 'update',
                'values': vals_destiny,
                'external_id': external_val,
                'odoo_id': record.id
            }
        else:
            data = {
                'action': 'insert',
                'values': vals_destiny,
                'external_id': False,
                'odoo_id': record.id
            }
        # enviamos el data
        response = self.sudo().sync_to_send(data)
        error = response.get('error', False)
        error_message = response.get('error_message', '')
        if not error:
            status = response.get('status', False)
            error_message = response.get('error_message', '')
            # si el retorno del ws es error o failed creamos una
            # traza en el historial
            if status in ['error', 'failed']:
                if generate_logs:
                    self.env['history.synchro.log'].sudo().create(
                        {
                            'trace': 'odoo-external',
                            'name': '%s %s' % (
                           _('Create') if not record.x_sys_id else _('Write'),
                            record._description),
                            'title': record.name,
                            'action_type': 'create' if not external_val else 'write',
                            'date_sync': fields.Datetime.now(),
                            'date_write': fields.Datetime.now(),
                            'state': 'failed',
                            'odoo_id': record.id,
                            'values_from_origin': str(vals_origin),
                            'values_to_destiny': str(vals_destiny),
                            'model': self.odoo_model.name,
                            'error_message': error_message
                        }
                    )
                self.env.cr.commit()
                raise ValidationError(error_message)
            else:
                # en el response debe venir en el value el campo con el valor
                # del id_externo de este modelo
                # buscamos que el campo que viene coincide con el campo referencia
                # en la configuracion, y si es asi, buscamos su campo analogo en
                # odoo e insertamos el valor
                vals_up = dict()
                external_val = response.get('external_id', False)
                vals_up.setdefault(field_in_odoo, external_val)
                if external_val:
                    ctx.update({'sync': True})
                    record.with_context(ctx).sudo().write(vals_up)
                    if generate_logs:
                        self.env['history.synchro.log'].sudo().create(
                            {
                                'trace': 'odoo-external',
                                'name': '%s %s' % (
                                _('Create') if not record.x_sys_id else _('Write'),
                                record._description),
                                'title': record.name,
                                'action_type': 'create' if not record.x_sys_id else 'write',
                                'date_sync': fields.Datetime.now(),
                                'date_write': fields.Datetime.now(),
                                'state': 'success',
                                'odoo_id': record.id,
                                'external_id': external_val,
                                'values_from_origin': str(vals_origin),
                                'values_to_destiny': str(vals_destiny),
                                'model': self.odoo_model.name,
                            }
                        )
                else:
                    if generate_logs:
                        error_message = _('The Web Service not confirm the record sent.')
                        self.env['history.synchro.log'].sudo().create(
                            {
                                'trace': 'odoo-external',
                                'name': '%s %s' % (
                                    _('Create') if not record.x_sys_id else _('Write'),
                                    record._description),
                                'title': record.name,
                                'action_type': 'create' if not record.x_sys_id else 'write',
                                'date_sync': fields.Datetime.now(),
                                'date_write': fields.Datetime.now(),
                                'state': 'failed',
                                'odoo_id': record.id,
                                'external_id': external_val,
                                'values_from_origin': str(vals_origin),
                                'values_to_destiny': str(vals_destiny),
                                'model': self.odoo_model.name,
                                'error_message': error_message
                            }
                        )
                    self.env.cr.commit()
                    raise ValidationError(error_message)
            self.env.cr.commit()
        else:
            raise ValidationError(error_message)

    def send_unlinked_records_real_time(self, record):
        """
        Function to send the deleted record in real time
        :param record: record to delete
        :return: void()
        """
        generate_logs = self.env['ir.config_parameter'].sudo().get_param(
            'w_sync.generate_logs', default=False)
        field_in_odoo = self.sudo().reference_field_odoo.name
        field_in_ext = self.sudo().reference_field_ext.code

        external_val = record.read([field_in_odoo])[0].get(
            field_in_odoo,
            False)
        vals = dict()
        if external_val:
            vals.setdefault(field_in_ext, external_val)
            data = {
                'action': 'delete',
                'external_id': external_val,
                'odoo_id': record.id
            }
            # enviamos el data de eliminacion
            response = self.sudo().sync_to_send(data)
            error = response.get('error', False)
            error_message = response.get('error_message', '')
            if not error:
                status = response.get('status', False)
                error_message = response.get('error_message', '')
                # si el retorno del ws es error o failed creamos una
                # traza en el historial
                if status in ['error', 'failed']:
                    if generate_logs:
                        self.env['history.synchro.log'].sudo().create(
                            {
                                'trace': 'odoo-external',
                                'name': _('Unlink %s') % record._description,
                                'title': record.name,
                                'action_type': 'unlink',
                                'date_sync': fields.Datetime.now(),
                                'date_write': fields.Datetime.now(),
                                'state': 'failed',
                                'odoo_id': record.id,
                                'model': self.odoo_model.name,
                                'error_message': error_message
                            }
                        )
                    self.env.cr.commit()
                    raise ValidationError(error_message)
                if status == 'success':
                    if generate_logs:
                        # si el retorno de ws es success creamos la traza
                        # y eliminamos el registro del modelo de registros eliminados
                        self.env['history.synchro.log'].sudo().create(
                            {
                                'trace': 'odoo-external',
                                'name': _('Unlink %s') % record._description,
                                'title': record.name,
                                'action_type': 'unlink',
                                'date_sync': fields.Datetime.now(),
                                'date_write': fields.Datetime.now(),
                                'state': 'success',
                                'odoo_id': record.id,
                                'external_id': external_val,
                                'model': self.odoo_model.name,
                            }
                        )
                    record.sudo().unlink()
                self.env.cr.commit()
            else:
                raise ValidationError(error_message)

    def create_record(self, values):
        """
        Function to create a record in Real Time from External System
        :param values: dict(): Values received from External System
        :return: integer: Id of created record
        """
        generate_logs = self.env['ir.config_parameter'].sudo().get_param(
            'w_sync.generate_logs', default=False)
        Model = self.env[self.odoo_model.model].sudo()
        mod_rec = Model
        values_updated = dict()
        ctx = self.env.context.copy()
        ctx.update({'sync': True})

        fields_received = list(values.keys())
        field_in_odoo = self.reference_field_odoo.name
        field_in_ext = self.reference_field_ext.code
        external_val = ''
        for f_r in fields_received:
            if f_r == field_in_ext:
                external_val = values[f_r]
                break

        fields_in_conf = self.sudo().mapped(
            'models_ids.external_field.code')
        for field in fields_in_conf:
            if field in values.keys():
                values_updated.setdefault(field, False)
                values_updated[field] = values[field]

        vals_origin, vals_destiny = self.sudo().convert_values_ext_odoo(
            values_updated)
        v_destiny = vals_destiny.copy()

        domain = [(field_in_odoo, '=', external_val)]
        mod_rec |= Model.search(domain, limit=1)
        if mod_rec:
            msg = _('A record with this Id (%s) already exists, you cannot '
                    'duplicate it, you can only submit a '
                    'modification.') % external_val
            if generate_logs:
                ip = self.env.context.get('ip', '')
                self.env['history.synchro.log'].sudo().create(
                    {
                        'trace': 'external-odoo',
                        'name': _('Create %s') % self.odoo_model.name,
                        'title': _('Unknown'),
                        'action_type': 'create',
                        'date_sync': fields.Datetime.now(),
                        'date_write': fields.Datetime.now(),
                        'state': 'failed',
                        'odoo_id': mod_rec.id,
                        'external_id': external_val,
                        'values_from_origin': str(values_updated),
                        'values_to_destiny': str(v_destiny),
                        'model': self.odoo_model.name,
                        'error_message': msg,
                        'ip': ip
                    }
                )
            raise ValidationError(msg)
        else:
            try:
                ip = self.env.context.get('ip', '')
                mod_rec |= Model.sudo().create(vals_destiny)
                self.run_code(mod_rec)
                if generate_logs:
                    self.env['history.synchro.log'].sudo().create(
                        {
                            'trace': 'external-odoo',
                            'name': _('Create %s') % self.odoo_model.name,
                            'title': mod_rec.name,
                            'action_type': 'create',
                            'date_sync': fields.Datetime.now(),
                            'date_write': fields.Datetime.now(),
                            'state': 'success',
                            'odoo_id': mod_rec.id,
                            'external_id': external_val,
                            'values_from_origin': str(
                                values_updated),
                            'values_to_destiny': str(v_destiny),
                            'model': self.odoo_model.name,
                            'ip': ip
                        }
                    )
                return mod_rec.id
            except Exception as e:
                if generate_logs:
                    ip = self.env.context.get('ip', '')
                    self.env['history.synchro.log'].sudo().create(
                        {
                            'trace': 'external-odoo',
                            'name': _('Create %s') % self.odoo_model.name,
                            'title': _('Unknown'),
                            'action_type': 'create',
                            'date_sync': fields.Datetime.now(),
                            'date_write': fields.Datetime.now(),
                            'state': 'failed',
                            'odoo_id': False,
                            'external_id': external_val,
                            'values_from_origin': str(values_updated),
                            'values_to_destiny': str(v_destiny),
                            'model': self.odoo_model.name,
                            'error_message': str(e),
                            'ip': ip
                        }
                    )
                if mod_rec:
                    mod_rec.unlink()
                raise e

    def write_record(self, record_id, values):
        """
        Function to update a record in Real Time from External System
        :param record_id: char: Id of record to insert in Odoo
        :param values: dict(): Values received form External System
        :return: booelan:
        """
        generate_logs = self.env['ir.config_parameter'].sudo().get_param(
            'w_sync.generate_logs', default=False)
        Model = self.env[self.odoo_model.model].sudo()
        mod_rec = Model
        values_updated = dict()
        ctx = self.env.context.copy()
        ctx.update(
            {
                'sync': True,
                'allowed_company_ids': self.env['res.company'].search([]).ids
            }
        )

        field_in_odoo = self.reference_field_odoo.name
        fields_in_conf = self.sudo().mapped(
            'models_ids.external_field.code')
        for field in fields_in_conf:
            if field in values.keys():
                values_updated.setdefault(field, False)
                values_updated[field] = values[field]

        vals_origin, vals_destiny = self.sudo().convert_values_ext_odoo(
            values_updated)
        v_destiny = vals_destiny.copy()

        domain = [(field_in_odoo, '=', record_id)]
        mod_rec |= Model.search(domain, limit=1)

        if mod_rec:
            id_rec = vals_destiny.get(field_in_odoo, '')
            if id_rec != record_id:
                msg = _('You are trying to change the external id: %s , which is not allowed.') % record_id
                if generate_logs:
                    ip = self.env.context.get('ip', '')
                    self.env['history.synchro.log'].sudo().create(
                        {
                            'trace': 'external-odoo',
                            'name': _('Write %s') % self.odoo_model.name,
                            'title': mod_rec.name,
                            'action_type': 'write',
                            'date_sync': fields.Datetime.now(),
                            'date_write': fields.Datetime.now(),
                            'state': 'failed',
                            'odoo_id': mod_rec.id,
                            'external_id': record_id,
                            'values_from_origin': str(values_updated),
                            'values_to_destiny': str(v_destiny),
                            'model': self.odoo_model.name,
                            'error_message': msg,
                            'ip': ip
                        }
                    )
                raise ValidationError(msg)
            try:
                mod_rec.with_context(ctx).sudo().write(vals_destiny)
                if generate_logs:
                    ip = self.env.context.get('ip', '')
                    self.env['history.synchro.log'].sudo().create(
                        {
                            'trace': 'external-odoo',
                            'name': _('Write %s') % self.odoo_model.name,
                            'title': mod_rec.name,
                            'action_type': 'write',
                            'date_sync': fields.Datetime.now(),
                            'date_write': fields.Datetime.now(),
                            'state': 'success',
                            'odoo_id': mod_rec.id,
                            'external_id': record_id,
                            'values_from_origin': str(
                                values_updated),
                            'values_to_destiny': str(v_destiny),
                            'model': self.odoo_model.name,
                            'ip': ip
                        }
                    )
                return mod_rec.id
            except Exception as e:
                if generate_logs:
                    ip = self.env.context.get('ip', '')
                    self.env['history.synchro.log'].sudo().create(
                        {
                            'trace': 'external-odoo',
                            'name': _('Write %s') % self.odoo_model.name,
                             'title': mod_rec.name,
                            'action_type': 'write',
                            'date_sync': fields.Datetime.now(),
                            'date_write': fields.Datetime.now(),
                            'state': 'failed',
                            'odoo_id': mod_rec.id,
                            'external_id': record_id,
                            'values_from_origin': str(values_updated),
                            'values_to_destiny': str(v_destiny),
                            'model': self.odoo_model.name,
                            'error_message': str(e),
                            'ip': ip
                        }
                    )
                raise e
        else:
            msg = _(
                'The record with Id (%s) not exist in Odoo.') % record_id
            raise ValidationError(msg)

    def unlink_record(self, record_id):
        """
        Function to unlink a record in Real Time from External System
        :param record_id: char: Id of record to delete in Odoo
        :return: boolean
        """
        generate_logs = self.env['ir.config_parameter'].sudo().get_param(
            'w_sync.generate_logs', default=False)
        Model = self.env[self.odoo_model.model].sudo()
        mod_rec = Model
        ctx = self.env.context.copy()
        ctx.update({'sync': True})
        field_in_odoo = self.reference_field_odoo.name
        domain = [(field_in_odoo, '=', record_id)]
        mod_rec |= Model.search(domain, limit=1)
        if mod_rec:
            id = mod_rec.id
            name = mod_rec.name
            mod_rec.with_context(ctx).sudo().unlink()
            try:
                if generate_logs:
                    self.env['history.synchro.log'].sudo().create(
                        {
                            'trace': 'external-odoo',
                            'name': _('Unlink %s') % self.odoo_model.name,
                            'title': name,
                            'action_type': 'unlink',
                            'date_sync': fields.Datetime.now(),
                            'date_write': fields.Datetime.now(),
                            'state': 'success',
                            'odoo_id': id,
                            'external_id': record_id,
                            'model': self.odoo_model.name
                        }
                    )
                return id
            except Exception as e:
                if generate_logs:
                    ip = self.env.context.get('ip', '')
                    self.env['history.synchro.log'].sudo().create(
                        {
                            'trace': 'external-odoo',
                            'name': _('Unlink %s') % self.odoo_model.name,
                            'title': name,
                            'action_type': 'unlink',
                            'date_sync': fields.Datetime.now(),
                            'date_write': fields.Datetime.now(),
                            'state': 'failed',
                            'odoo_id': id,
                            'external_id': record_id,
                            'model': self.odoo_model.name,
                            'error_message': str(e),
                            'ip': ip
                        }
                    )
                raise e
        else:
            msg = _(
                'The record with Id (%s) not exist in Odoo.') % record_id
            raise ValidationError(msg)

    @api.model
    def convert_values_ext_odoo(self, values):
        """
        Convierta los valores del sistema externo a odoo
        :param values: dict(): registry values ​​in the external system
        :return: tuple(): external system values ​​converted to odoo
        """
        vals_origin = values
        vals_destiny = dict()
        for val in values.keys():
            field_line = self.models_ids.filtered(lambda x: x.external_field.code == val and x.activo)
            odoo_field = field_line.name_f
            reference_field = field_line.reference_field
            if odoo_field.ttype in ['many2one', 'many2many', 'one2many']:
                if values[val]:
                    if odoo_field.ttype == 'many2one':
                        # Mejora realizada: Si no tiene configuracion en el campo 'reference_field' se asume
                        # que se conoce el id de Odoo y se esta pasando ese id
                        if reference_field:
                            domain = [(reference_field, '=', values[val])]
                            f_id = self.env[odoo_field.relation]. \
                                search(domain, limit=1)
                            if f_id:
                                vals_destiny.setdefault(odoo_field.name,
                                                        f_id.id)
                            else:
                                raise ValidationError(
                                    _("The field %s could not "
                                      "be found") % val)
                        else:
                            vals_destiny.setdefault(odoo_field.name, values[val])

                    elif odoo_field.ttype == 'one2many':
                        value_one2many = []
                        for id in values[val]:
                            field_one2many = self.env[
                                odoo_field.relation]. \
                                search([(reference_field, '=',
                                         id)])

                            if field_one2many:
                                value_one2many.append(
                                    (4, field_one2many.id))
                            else:
                                raise ValidationError(
                                    _("The field %s could not "
                                      "be found") % val)
                        vals_destiny.setdefault(odoo_field.name,
                                             value_one2many)

                    elif odoo_field.ttype == 'many2many':
                        value_many2many = []
                        for id in values[val]:
                            field_many2many = self.env[
                                odoo_field.relation]. \
                                search([(reference_field,
                                         '=', id)])
                            if field_many2many:
                                value_many2many.append(
                                    (4, field_many2many.id))
                            else:
                                raise ValidationError(
                                    _("The field %s could not "
                                      "be found") % val)
                        vals_destiny.setdefault(odoo_field.name,
                                             value_many2many)
                else:
                    vals_destiny.setdefault(odoo_field.name, False)
            else:
                vals_destiny.setdefault(odoo_field.name, values[val])
        return vals_origin, vals_destiny

    @api.model
    def convert_values_odoo_ext(self, values):
        """
        Convert the values ​​from odoo to the external system
        :param values: dict(): registry values ​​in odoo
        :return: tuple(): odoo values ​​converted to external system
        """
        vals_origin = dict()
        vals_destiny = dict()
        obj_id = values.get('obj_id', False)
        if self.direction in ['odoo2ext', 'bidirectional']:
            obj = self.env[self.reference_field_odoo.model].browse(obj_id)
            list_fields = list(values.keys())
            fiels_to_sent = self.models_ids.filtered(lambda x: x.name_f.name in list_fields and x.activo)
            for rec in fiels_to_sent:
                field = rec.name_f.name
                if rec.type in ['many2one', 'one2many', 'many2many']:
                    if rec.reference_field in obj.mapped('%s' % (field,)).fields_get().keys():
                        val = obj.mapped(
                            '%s.%s' % (field, rec.reference_field)
                        )
                        val1 = obj.mapped(
                            '%s.%s' % (field, 'id')
                        )
                        if not val:
                            val = ''
                            val1 = ''
                        if val and rec.type == 'many2one':
                            val = val[0]
                        if val1 and rec.type == 'many2one':
                            val1 = val1[0]
                    else:
                        msg = _('The %s model does not have the %s field.') % (obj.mapped('%s' % (field,))._description, rec.reference_field)
                        rec.details = msg
                        continue
                elif rec.type in ['date', 'datetime']:
                    date = obj.mapped(field)[0]
                    if rec.type == 'date':
                        val = fields.Date.to_string(date) if date else False
                        val1 = fields.Date.to_string(date)if date else False
                    elif rec.type == 'datetime':
                        val = fields.Datetime.to_string(date) if date else False
                        val1 = fields.Datetime.to_string(date) if date else False
                else:
                    if obj and field in obj and (field not in values or self.env.context.get('cron', False)):
                        val = obj.mapped(field)[0]
                        val1 = val
                    else:
                        val = values.get(field, '')
                        val1 = val
                if rec.operator and rec.operator == 'not_equal':
                    val = not val

                vals_destiny[rec.external_field.code] = val
                vals_origin[rec.name_f.name] = val1
        return vals_origin, vals_destiny

    def sync_to_send(self, data):
        """
        Function to send the data to the ws
        :param data: dict(): dictionary with the data of the records to send
        :return: dict(): dictionary with confirmation of records
        """
        for sync in self:
            if sync.ws_url_id:
                res = sync.ws_url_id.send_data(data)
                return res
            else:
                return {
                    'status': 'error',
                    'error_message': _('The Web Service to send data is not '
                                   'define in synchro object %s') % (sync.name,)
                }

    def sync_to_receive(self, data={}):
        """
        Function to receive data from ws
        :param data: dict(): dictionary with parameters
        :return: dict(): dictionary with data from the records to be synchronized
        """
        for sync in self:
            if sync.ws_url_id:
                res = sync.ws_url_id.receive_data(data)
                return res
            else:
                return {
                    'status': 'error',
                    'error_message': _('The Web Service to synchro data is not '
                                   'defined in synchro object %s') % sync.name
                }

    def sync_to_confirm(self, data):
        """
        Function to send confirmation
        :param data: dict(): dictionary with confirmation of synchronized record
        :return: dict(): confirmation return
        """
        for sync in self:
            ws = sync.ws_url_id
            if ws and ws.need_confirmation:
                if ws.url_confirmation:
                    res = sync.ws_url_id.send_confirmation(data)
                    return res
                return {
                    'status': 'error',
                    'error_message': _('The Web Service to send confirmation is not '
                                       'define in web service %s') % ws.name
                }
            else:
                return {
                    'status': 'success',
                    'error_message': False
                }

    def nothing_to_do(self):
        pass

    @api.model
    def _get_eval_context(self, record):
        cr = self.env.cr
        env = self.env
        model = self.env[self._name]
        eval_context = {
            'env': env,
            'model': model,
            'record': record,
            'UserError': UserError,
            'cr': cr,
            'date': fields.Date
        }
        return eval_context

    def run_code(self, record=False):
        if self.code and record and self.code:
            try:
                eval_context = self._get_eval_context(record=record)
                # res = getattr(record.sudo(), self.code)()
                res = eval(self.code, eval_context, mode='exec', nocopy=True)
                return res
            except Exception as e:
                raise e
                # try:
                #     body = _("<p>The following error was generated when calling "
                #              "the function %s:</p> \n"
                #              "<b>%s</b>") % (self.code, e)
                #     record.message_post(body=body)
                #     raise body
                # except Exception as e:
                #     pass
        return False
