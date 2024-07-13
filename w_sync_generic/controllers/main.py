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
import json
import werkzeug
from odoo import _
from odoo import SUPERUSER_ID, api, models
from odoo.http import request, Controller, route
from odoo.osv import expression
from functools import wraps
import logging
_logger = logging.getLogger(__name__)

DOM = [
    ('synchro_mode', '=', 'real_time'),
    ('direction', 'in', ['ext2odoo', 'bidirectional'])
]
import threading

# Crear un bloqueo global
lock = threading.Lock()



class RestWebServices(Controller):

    def __authenticate(func):
        @wraps(func)
        def wrapped(inst, **kwargs):
            lock.acquire()
            inst._data = request.httprequest.data and json.loads(
                request.httprequest.data.decode('utf-8')) or {}
            inst.ctype = request.httprequest.headers.get(
                'Content-Type') == 'text/xml' and 'text/xml' or 'json'
            inst._auth = inst._authenticate(**kwargs)
            lock.release()
            return func(inst, **kwargs)

        return wrapped

    def _response(self, api, response, ctype='json'):
        if ctype == 'json':
            mime = 'application/json; charset=utf-8'
            body = json.dumps(response)
        else:
            mime = 'text/xml'
            body = self._wrap2xml(api, response)
        headers = [
            ('Content-Type', mime),
            ('Content-Length', len(body))
        ]
        return werkzeug.wrappers.Response(body, headers=headers)

    def _check_api_key(self, api_key):
        response = {
            'status': 'success',
            'error_message': ''
        }
        if not api_key:
            response['status'] = 'failed'
            response['error_message'] = _("Invalid/Missing Api Key!")
            return response
        try:
            apikey = request.env['ir.config_parameter'].sudo().get_param(
                'w_sync.api_key', default='')
            if apikey:
                if apikey == api_key:
                    response['status'] = 'success'
                else:
                    response['status'] = 'failed'
                    response['error_message'] = _("API Key is invalid!")
            else:
                response['status'] = 'failed'
                response['error_message'] = _("Api key not configurated "
                                              "in system!")
                return response

        except Exception as e:
            response['status'] = 'failed'
            response['error_message'] = _(
                "Login Failed: %r") % str(e)
        return response

    def _authenticate(self, **kwargs):
        _logger.warning(request.httprequest.headers)
        if request.httprequest.headers.get('Apikey'):
            api_key = request.httprequest.headers.get('Apikey') or None
        else:
            api_key = False
        response = self._check_api_key(api_key)
        response.update(kwargs)
        return response

    @route(['/sync/<string:model>/create'], type='json', auth="public",
           csrf=False, methods=['POST'])
    @__authenticate
    def createRecord(self, model, **kwargs):
        response = self._auth
        if response.get('status', '') == 'success':
            try:
                values = self._data
                synchro_object = request.env['synchro.obj'].sudo()
                domain = ('external_model_name', '=', model),
                dom = expression.AND([DOM, domain])
                synchro_id = synchro_object.search(dom, limit=1)
                api_line = synchro_id.api_ids.filtered(lambda x: x.action == 'insert')
                ip = request.httprequest.environ['REMOTE_ADDR'] or False
                context = {
                    'ip': ip
                }
                if api_line:
                    context.update(eval(api_line[-1].context) if api_line[-1].context else {})
                if synchro_id:
                    if synchro_id.mapped('api_ids').filtered(
                            lambda x: x.action == 'insert' and x.activ):
                        odoo_id = synchro_id.with_context(context).create_record(values)
                        response['odoo_id'] = str(odoo_id)
                    else:
                        response['error_message'] = _(
                            "The Web Service for this action is not active.")
                        response['status'] = 'failed'
                else:
                    response['error_message'] = _("There is no Synchronization "
                                                  "Object configured for this "
                                                  "model.")
                    response['status'] = 'failed'
            except Exception as e:
                response['error_message'] = "ERROR: %r. Values received %r" % (
                str(e), values)
                response['status'] = 'failed'
        del response['model']
        return response

    @route(['/sync/<string:model>/<string:record_id>'], type='json',
           auth="none", methods=['PUT'], csrf=False)
    @__authenticate
    def updateRecord(self, model, record_id, **kwargs):
        response = self._auth
        if response.get('status') == 'success':
            try:
                values = self._data
                synchro_object = request.env['synchro.obj'].sudo()
                domain = ('external_model_name', '=', model),
                dom = expression.AND([DOM, domain])
                synchro_id = synchro_object.search(dom, limit=1)
                api_line = synchro_id.api_ids.filtered(lambda x: x.action == 'update')
                ip = request.httprequest.environ['REMOTE_ADDR'] or False
                context = {
                    'ip': ip
                }
                if api_line:
                    context.update(eval(api_line[-1].context) if api_line[-1].context else {})
                if synchro_id:
                    if synchro_id.mapped('api_ids').filtered(
                            lambda x: x.action == 'update' and x.activ):
                        odoo_id = synchro_id.with_context(context).write_record(record_id, values)
                        response['odoo_id'] = str(odoo_id)
                    else:
                        response['error_message'] = _(
                            "The Web Service for this action is not active.")
                        response['status'] = 'failed'

                else:
                    response['error_message'] = _("There is no Synchronization "
                                                  "Object configured for this "
                                                  "model.")
                    response['status'] = 'failed'
            except Exception as e:
                response['error_message'] = "ERROR: %r. Values received %r" % (str(e), values)
                response['status'] = 'failed'
        del response['record_id']
        del response['model']
        return response

    @route(['/sync/<string:model>/<string:record_id>'], type='http',
           auth="none", methods=['DELETE'], csrf=False)
    @__authenticate
    def deleteRecord(self, model, record_id, **kwargs):
        response = self._auth
        if response.get('status') == 'success':
            try:
                synchro_object = request.env['synchro.obj'].sudo()
                domain = ('external_model_name', '=', model),
                dom = expression.AND([DOM, domain])
                synchro_id = synchro_object.search(dom, limit=1)
                api_line = synchro_id.api_ids.filtered(lambda x: x.action == 'delete')
                ip = request.httprequest.environ['REMOTE_ADDR'] or False
                context = {
                    'ip': ip
                }
                if api_line:
                    context.update(eval(api_line[-1].context) if api_line[-1].context else {})
                if synchro_id:
                    if synchro_id.mapped('api_ids').filtered(
                            lambda x: x.action == 'delete' and x.activ):
                        odoo_id = synchro_id.with_context(context).unlink_record(record_id)
                        response['odoo_id'] = str(odoo_id)
                    else:
                        response['error_message'] = _(
                            "The Web Service for this action is not active.")
                        response['status'] = 'failed'
                else:
                    response['error_message'] = _("There is no Synchronization "
                                                  "Object configured for this "
                                                  "model.")
                    response['status'] = 'failed'
            except Exception as e:
                response['error_message'] = "ERROR: %r" % str(e)
                response['status'] = 'failed'
        del response['record_id']
        del response['model']
        return self._response(model, response, self.ctype)

    @route(['/trigger/<string:key>'], type='json', auth="public",
           csrf=False, methods=['POST'])
    @__authenticate
    def function_trigger(self, key, **kwargs):
        response = self._auth
        try:
            values = self._data
            function_trigger_obj = request.env['function.trigger'].sudo()
            domain = [('key', '=', key)]
            obj_id = function_trigger_obj.search(domain, limit=1)
            ip = request.httprequest.environ['REMOTE_ADDR'] or False
            context = {
                'ip': ip
            }
            if obj_id:
                obj_id.with_context(context).run_code(values)
            else:
                response['error_message'] = _("There is no Function Trigger "
                                              "Object configured for this "
                                              "key.")
                response['status'] = 'failed'
        except Exception as e:
            response['error_message'] = "ERROR: %r. Values received %r" % (
                str(e), values)
            response['status'] = 'failed'
        return response
