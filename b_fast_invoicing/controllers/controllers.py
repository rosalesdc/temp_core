
# -*- encoding: utf-8 -*-
#
# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2023 Birtum - https://www.birtum.com
# All Rights Reserved.
#
# Developer(s): Eddy Luis Perez Vila
#               epv@birtum.com
#########################################################
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################
import json
import logging
from stdnum.mx.rfc import format, validate, InvalidComponent, InvalidFormat, InvalidLength, InvalidChecksum
import uuid

from odoo import SUPERUSER_ID, _, http, fields
from odoo.exceptions import AccessError, MissingError, UserError, ValidationError
from odoo.http import request

import werkzeug
import werkzeug.urls

logger = logging.getLogger(__name__)


class FastInvoicing(http.Controller):

    def _get_order_by_ref(self, search):
        '''Busca la orden de venta en PoS orders, si existe, genera un token de acceso.
           Si no existe, busca la orden en ventas y genera un token de acceso.
           Retorna diccionario con token, busqueda y si es venta de PoS'''
           
        #TODO  Investigar porque no imprime 
        allowed = True
        order = request.env['pos.order'].with_user(SUPERUSER_ID).search([
            ('invoicing_ref', '=', search)
        ], limit=1)
        is_pos = bool(order)
        if order:
            order.generate_access_token()
        if not order:
            order = request.env['sale.order'].with_user(SUPERUSER_ID).search([
                ('invoicing_ref', '=', search),
            ], limit=1)
            order.write({'access_token': str(uuid.uuid4())})
        if order:
            if order.company_id.define_time_create_invoice != 'not_deny':
                today = fields.Datetime.today()
                days = (today - order.date_order).days
                if order.company_id.define_time_create_invoice == 'month' and order.date_order.month != today.month:
                    allowed = False
                if order.company_id.define_time_create_invoice == 'x_days' and days >  order.company_id.limit_days_to_invoice:
                    allowed = False
        if order and order.state != "sale" and order.state != "done":
            return {
                'is_allowed': allowed,
                'is_not_sale': True,
                'search': search,
                'is_pos': is_pos,
            }
        return {
            'is_allowed': allowed,
            'access_token': order.access_token,
            'search': search,
            'is_pos': is_pos,
        }
    
    
    @http.route('/autofactura/registred/<string:access_token>', auth='public', website=True, methods=['POST'])
    def registred_partner(self, access_token, **post):
        # BROWSE ORDER
        try:
            new_partner_id = request.env['res.partner'].with_user(SUPERUSER_ID).create({
                    'name': post.get('partner_name', False),
                    'phone': post.get('partner_phone', False),
                    'email': post.get('partner_email', False),
                    'vat': post.get('test_vat', False),
                    'mobile': post.get('partner_movile', False),
                    'street': post.get('partner_street', False),
                    'zip': post.get('partner_zip', False),
                    'city': post.get('partner_city', False),
                    'state_id': int(post.get('partner_state_id')) if post.get('partner_state_id') else False,
                    'country_id': int(post.get('partner_country_id')) if post.get('partner_country_id') else False,
                    'l10n_mx_edi_fiscal_regime': post.get('l10n_mx_edi_fiscal_regime', False),
                })
            return request.render('b_fast_invoicing.client_header', {
                'l10n_mx_edi_fiscal_regime': self.get_l10n_mx_edi_fiscal_regime(),
                'country': self.get_country(),
                'state_id': self._get_state_id(),
                'acces_token': str(uuid.uuid4()),
                'vat_cont': post.get('test_vat', False),
                'message': _('The client has been created successfully')
            })
        except Exception as e:
            return request.render('b_fast_invoicing.client_header', {
                'l10n_mx_edi_fiscal_regime': self.get_l10n_mx_edi_fiscal_regime(),
                'country': self.get_country(),
                'state_id': self._get_state_id(),
                'acces_token': str(uuid.uuid4()),
                'vat_cont': post.get('test_vat', False),
                'message': e
            })
    
    @http.route('/autofactura/client', auth='public', website=True)
    def index(self,message=False, **kw):  
        return request.render('b_fast_invoicing.client_header', {
            'l10n_mx_edi_fiscal_regime': self.get_l10n_mx_edi_fiscal_regime(),
            'country': self.get_country(),
            'state_id': self._get_state_id(),
            'acces_token': str(uuid.uuid4()),
            'vat_cont': False,
            'message': 'Desde esta pantalla puede buscar los contactos y registrarlos segun el RFC.'
         })
        
        
    @http.route('/autofactura/call/<string:vat>', auth='public', website=True)
    def index_autofactura_call(self,message=False, vat=False, **kw):  
        return request.redirect('/autofactura/' + vat)
        
    @http.route(['/autofactura', '/autofactura/<string:vat>'], auth='public', website=True)
    def index_autofactura(self,message=False, vat=False, **kw):  
        return request.render('b_fast_invoicing.invoicing_header', {
            'vat_cont': vat,
            'message': message
         })
        
    @http.route('/autofactura/search', auth='public', website=True, type='json')
    def search_order(self, search=''):
        return self._get_order_by_ref(search)
    
    @http.route('/autofactura/search/not_allowed', auth='public', website=True, methods=['GET'])
    def render_not_allowed(self, search_query):
        return request.render('b_fast_invoicing.not_allowed_to_invoice_alert', {
            'search': search_query,
        })
        
    @http.route('/autofactura/search/not_confirmed', auth='public', website=True, methods=['GET'])
    def render_not_confirmed(self, search_query):
        return request.render('b_fast_invoicing.not_confirmed_alert', {
            'search': search_query,
        })
        
    @http.route('/autofactura/search/not_found', auth='public', website=True, methods=['GET'])
    def render_no_search(self, search_query):
        return request.render('b_fast_invoicing.dismissible_alert', {
            'search': search_query,
        })
        
    @http.route('/autofactura/search/not_found/null', auth='public', website=True, methods=['GET'])
    def render_search_null(self):
        return request.render('b_fast_invoicing.dismissible_alert_null', {})
    
    @http.route(['/autofactura/pedido/tpv/<string:access_token>', '/autofactura/pedido/tpv/<string:vat>/<string:access_token>'], auth='public', website=True)
    def pos_order_index(self, access_token, vat=False, *kwargs):
        order = request.env['pos.order'].with_user(SUPERUSER_ID).search([
            ('access_token', '=', access_token)], limit=1)
        if vat:
            partner = request.env['res.partner'].with_user(SUPERUSER_ID).search([
                ('vat', '=', vat)], limit=1)
        else:
            partner = False
        go_url = '#'
        inv = order.account_move
        if inv and inv.access_token:
            go_url = '/autofactura/' + inv.access_token + '/' + order.access_token + '?tpv=1'
        return request.render('b_fast_invoicing.invoicing_order_page', {
            'order': order,
            'search': '',
            'partner': partner if partner else False,
            'is_pos': True,
            'vat_cont': vat if vat else '',
            'cfdi': self.get_cfdi_usage(),
            'invoice': inv,
            'go_url': go_url
        })

    @http.route(['/autofactura/invoicing/pos/<string:access_token>',
                 '/autofactura/invoicing/pos/<string:vat>/<string:access_token>'], auth='public', website=True)
    def invoicing_pos_index(self, access_token, vat=False, **post):
        order = request.env['pos.order'].with_user(SUPERUSER_ID).search([
            ('access_token', '=', access_token)
        ], limit=1)
        partner = order.partner_id

        p_rfc = partner.vat
        vats = []
        if p_rfc:
            vats = [(p_rfc, p_rfc)] + [(partner.vat, partner.vat)]
        return request.render('b_fast_invoicing.invoicing_invoicing_modal', {
            'order': order,
            'partner': order.partner_id,
            'tpv': 1,
            'vat': vat if vat else '',
            'cfdi_use': post.get('cfdi_use'),
            'cfdi': self.get_cfdi_usage(),
            'payment_method': self.get_payment_method(),
            'l10n_mx_edi_fiscal_regime': self.get_l10n_mx_edi_fiscal_regime(),
            'vats': vats
        })

    def get_cfdi_usage(self):
        return [
            ('G01', _('Adquisición de mercancías')),
            ('G02', _('Devoluciones, descuentos o bonificaciones')),
            ('G03', _('Gastos en general')),
            ('I01', _('Constructions')),
            ('I02', _('Mobilario y equipo de oficina por inversiones')),
            ('I03', _('Equipo de transporte')),
            ('I04', _('Equipo de cómputo y accesorios')),
            ('I05', _('Dados, troqueles, moldes, matrices y herramental')),
            ('I06', _('Comunicaciones telefónicas')),
            ('I07', _('Comunicaciones satelitales')),
            ('I08', _('Otra maquinaria y equipo')),
            ('D01', _('Honorarios médicos, dentales y gastos hospitalarios.')),
            ('D02', _('Gastos médicos por incapacidad o discapacidad')),
            ('D03', _('Gastos funerales')),
            ('D04', _('Donativos')),
            ('D05', _('Intereses reales efectivamente pagados por créditos hipotecarios (casa habitación).')),
            ('D06', _('Aportaciones voluntarias al SAR')),
            ('D07', _('Primas por seguros de gastos médicos')),
            ('D08', _('Gastos de transportación escolar obligatoria')),
            ('D09', _('Depósitos en cuentas para el ahorro, primas que tengan como base planes de pensiones.')),
            ('D10', _('Pagos por servicios educativos (colegiaturas)')),
            ('P01', _('Por definir')),
        ]
        
    def get_payment_method(self):
        val = []
        for r in request.env['l10n_mx_edi.payment.method'].with_user(SUPERUSER_ID).search([]):
            val.append((r.id, r.name))
        return val
    
    def get_country(self):
        val = []
        for r in request.env['res.country'].with_user(SUPERUSER_ID).search([]):
            val.append((r.id, r.name))
        return val
    
    def _get_state_id(self):
        val = []
        for r in request.env['res.country.state'].with_user(SUPERUSER_ID).search([]):
            if r.country_id.name == 'México' or r.country_id.name == 'Mexico':
                val.append((r.id, r.name))
        return val
    
    def get_l10n_mx_edi_fiscal_regime(self):
        return [
            ('601', 'General de Ley Personas Morales'),
            ('603', 'Personas Morales con Fines no Lucrativos'),
            ('605', 'Sueldos y Salarios e Ingresos Asimilados a Salarios'),
            ('606', 'Arrendamiento'),
            ('607', 'Régimen de Enajenación o Adquisición de Bienes'),
            ('608', 'Demás ingresos'),
            ('609', 'Consolidación'),
            ('610', 'Residentes en el Extranjero sin Establecimiento Permanente en México'),
            ('611', 'Ingresos por Dividendos (socios y accionistas)'),
            ('612', 'Personas Físicas con Actividades Empresariales y Profesionales'),
            ('614', 'Ingresos por intereses'),
            ('615', 'Régimen de los ingresos por obtención de premios'),
            ('616', 'Sin obligaciones fiscales'),
            ('620', 'Sociedades Cooperativas de Producción que optan por diferir sus ingresos'),
            ('621', 'Incorporación Fiscal'),
            ('622', 'Actividades Agrícolas, Ganaderas, Silvícolas y Pesqueras'),
            ('623', 'Opcional para Grupos de Sociedades'),
            ('624', 'Coordinados'),
            ('625', 'Régimen de las Actividades Empresariales con ingresos a través de Plataformas Tecnológicas'),
            ('626', 'Régimen Simplificado de Confianza - RESICO'),
            ('628', 'Hidrocarburos'),
            ('629', 'De los Regímenes Fiscales Preferentes y de las Empresas Multinacionales'),
            ('630', 'Enajenación de acciones en bolsa de valores')]
    
    @http.route('/autofactura/<string:access_token>/direct', auth='public', website=True, methods=['POST'])
    def direct_invoicing(self, access_token, **post):
        # BROWSE ORDER
        tpv = bool(post.get('tpv', 0))
        env_obj = tpv and 'pos.order' or 'sale.order'
        sale_order = request.env[env_obj].with_user(SUPERUSER_ID).search([
            ('access_token', '=', access_token)
        ], limit=1)
        partner = sale_order.partner_id

        if not partner:
            return '/autofactura?message=no-partner'

        if not partner.vat:
            return ''

        if tpv:
            # MAKE INVOICE
            try:
                invoices = sale_order.with_context(
                    from_auto_invoice=True).action_pos_order_invoice().get('res_id', False)
                invoices = request.env['account.move'].with_user(SUPERUSER_ID).browse(invoices)
            except UserError as ue:
                request.env.cr.rollback()
                params = {
                    'token': access_token,
                    'message': ue.name or ue.value
                }
                return '/autofactura/error/notify?' + werkzeug.urls.url_encode(params)
        else:
            # MAKE INVOICE
            try:
                invoices = sale_order.with_context(from_auto_invoice=True)._create_invoices()
            except UserError as ue:
                request.env.cr.rollback()
                params = {
                    'token': access_token,
                    'message': ue.name or ue.value
                }
                return '/autofactura/error/notify?' + werkzeug.urls.url_encode(params)

        for inv in invoices.sorted('move_type'):
            payment_method = False
            # POST A MESSAGE
            inv.message_post(body=_('This invoice has been created by user {}').format(
                inv.partner_id.display_name))
            if inv.move_type == 'out_invoice':
                auto_payment_policy = 'PPD'
                payment_obj = request.env['account.payment']
                payments = payment_obj.with_user(SUPERUSER_ID).search([
                    ('partner_id', '=', partner.id),
                    ('payment_type', '=', 'inbound'),
                    ('partner_type', '=', 'customer'),
                    ('state', '=', 'posted')
                ])
                move_lines = payments.mapped('move_line_ids').filtered(
                    lambda ml: not ml.reconciled and ml.credit > 0.0).sorted(
                    lambda ml: ml.get_amount_to_show(inv), reverse=True)
                if move_lines:
                    payment_method = move_lines[:1].payment_id.l10n_mx_edi_payment_method_id.id
                    if sum([ml.get_amount_to_show(inv) for ml in move_lines]) >= inv.amount_total:
                        auto_payment_policy = 'PUE'
                write_data = {
                    'access_token': str(uuid.uuid4()),
                    'l10n_mx_edi_usage': post.get('cfdi_use', False),
                    'auto_payment_policy': auto_payment_policy,
                    'l10n_mx_edi_payment_method_id': payment_method
                }
                if payment_method:
                    write_data['l10n_mx_edi_payment_method_id'] = payment_method
                inv.write(write_data)
            # CONFIRM INVOICE
            confirm_context = dict(
                disable_after_commit=True,
                force_company=request.env.user.company_id.id,
                pos_picking_id=tpv and sale_order.picking_id or False
            )
            try:
                inv.with_context(**confirm_context).action_post()
            except Exception as e:
                request.env.cr.rollback()
                params = {
                    'token': access_token,
                    'message': str(e)
                }
                return request.redirect(
                    '/autofactura/error/notify?' + werkzeug.urls.url_encode(params))
            # MAKING PAYMENTS
            try:
                inv.with_context(fast_invoicing_apply_payment=True).fast_invoicing_auto_pay()
            except Exception as e:
                request.env.cr.rollback()
                params = {
                    'token': access_token,
                    'message': str(e)
                }
                return '/autofactura/error/notify?' + werkzeug.urls.url_encode(params)
            # SEND MAIL AUTOMATIC
            if inv.move_type == 'out_invoice':
                self._action_send_email(inv.access_token)
                url = '/autofactura/' + inv.access_token + '/' + sale_order.access_token
                params = {}
                if tpv:
                    params['tpv'] = 1
                if params:
                    url += '?%s' % werkzeug.urls.url_encode(params)
                return url
        return '/autofactura?message=no-invoice'


    @http.route('/autofactura/<string:access_token>/submit', auth='public', website=True, methods=['POST'])
    def invoicing_submit(self, access_token, **post):

        # BROWSE ORDER
        tpv = bool(post.get('tpv', 0))
        env_obj = tpv and 'pos.order' or 'sale.order'
        sale_order = request.env[env_obj].with_user(SUPERUSER_ID).search([
            ('access_token', '=', access_token)
        ], limit=1)
        
        
        if not sale_order.partner_id:
            # Comentamos el comportamiento anterior, ya no usaremos un
            # partner por defecto, creamos un nuevo partner con los datos
            # que nos mandan
            if post.get('vat', False):
                partner_id = request.env['res.partner'].with_user(SUPERUSER_ID).\
                    search([('vat', 'ilike', post['vat'])], limit=1)
                if partner_id:
                    sale_order.partner_id = partner_id.id
                    if not partner_id.l10n_mx_edi_fiscal_regime:
                        partner_id.l10n_mx_edi_fiscal_regime = post.get('l10n_mx_edi_fiscal_regime', False)
                else:
                    new_partner_id = request.env['res.partner'].with_user(SUPERUSER_ID).create({
                        'vat': post.get('vat', False),
                        'name': post.get('name', False),
                        'phone': post.get('phone', False),
                        'email': post.get('email', False),
                        'l10n_mx_edi_fiscal_regime': post.get('l10n_mx_edi_fiscal_regime', False),
                    })
                    sale_order.partner_id = new_partner_id.id
        if tpv:
            # MAKE INVOICE
            try:
                invoices = sale_order.with_user(SUPERUSER_ID).with_context(
                    from_auto_invoice=True).action_pos_order_invoice().get('res_id', False)
                invoices = request.env['account.move'].with_user(SUPERUSER_ID).browse(invoices)
                if post.get('payment_method'):
                    invoices.l10n_mx_edi_payment_method_id = int(post.get('payment_method'))
                partner_id = request.env['res.partner'].with_user(SUPERUSER_ID).\
                    search([('vat', 'ilike', post['vat'])], limit=1)
                if partner_id:
                    invoices.partner_id = partner_id.id
                sale_order.from_auto_invoice = True
            except UserError as ue:
                request.env.cr.rollback()
                params = {
                    'token': access_token,
                    'message': ue.name or ue.value
                }
                return request.redirect(
                    '/autofactura/error/notify?' + werkzeug.urls.url_encode(params))
        else:
            # MAKE INVOICE

            try:
                invoices = sale_order.with_context(from_auto_invoice=True)._create_invoices()
                if post.get('payment_method'):
                    invoices.l10n_mx_edi_payment_method_id = int(post.get('payment_method'))
                partner_id = request.env['res.partner'].with_user(SUPERUSER_ID).\
                    search([('vat', 'ilike', post['vat'])], limit=1)
                if partner_id:
                    invoices.partner_id = partner_id.id
                    sale_order.partner_invoice_id = partner_id.id
                sale_order.from_auto_invoice = True
            except UserError as ue:
                request.env.cr.rollback()
                params = {
                    'token': access_token,
                    'message': ue.name or ue.value
                }
                return request.redirect('/autofactura/error/notify?' + werkzeug.urls.url_encode(params))

        for inv in invoices.sorted(lambda x: x.move_type, reverse=True):
            payment_method = False
            # POST A MESSAGE
            inv.message_post(body=_('This invoice has been created by user {}').format(
                inv.partner_id.display_name))
            if inv.move_type == 'out_invoice':
                auto_payment_policy = 'PPD'
                payment_obj = request.env['account.payment']
                payments = payment_obj.with_user(SUPERUSER_ID).search([
                    ('partner_id', '=', sale_order.partner_id.id),
                    ('payment_type', '=', 'inbound'),
                    ('partner_type', '=', 'customer'),
                    ('state', '=', 'posted')
                ])
                move_lines = payments.mapped('line_ids').filtered(
                    lambda ml: not ml.reconciled and ml.credit > 0.0).sorted(
                    lambda ml: ml.get_amount_to_show(inv), reverse=True)
                if move_lines:
                    payment_method = move_lines[:1].payment_id.l10n_mx_edi_payment_method_id.id
                    if sum([ml.get_amount_to_show(inv) for ml in move_lines]) >= inv.amount_total:
                        auto_payment_policy = 'PUE'
                write_data = {
                    'access_token': str(uuid.uuid4()),
                    'l10n_mx_edi_usage': post.get('cfdi_use', False),
                    'auto_payment_policy': auto_payment_policy,
                    'auto_invoice_vat': post.get('vat', False),
                    'l10n_mx_edi_payment_method_id': int(post.get('payment_method')) if post.get('payment_method') else ''
                }
                if payment_method:
                    write_data['l10n_mx_edi_payment_method_id'] = payment_method
                else:
                    if tpv:
                        # Hemos hecho que coincida las formas de pagos de la localizacion
                        # con los diarios, antes solo mapeaba banco, ahora las mapeamos todas
                        # asi en caso de que la orden venga del tpv y con pagos podemos halar esa forma
                        # desde ahi
                        pos_payment_line = sale_order.payment_ids[:1]
                        payment_method = pos_payment_line.payment_method_id.l10n_mx_edi_payment_method_id.id
                        if not pos_payment_line.payment_method_id.l10n_mx_edi_payment_method_id:
                            payment_method = int(post.get('payment_method')) if post.get('payment_method') else False
                        write_data['l10n_mx_edi_payment_method_id'] = payment_method

                inv.write(write_data)
            # CONFIRM INVOICE
            confirm_context = dict(
                disable_after_commit=True,
                with_company=request.env.user.company_id.id,
                pos_picking_id=tpv and sale_order.picking_ids or False
            )
            # Añadimos esta validacion pq ya la funcion
            # _create_invoices trata de postear la factura, nosotros
            # solo lo hacemos si no viene posteada
            if inv.state != 'posted':
                try:
                    inv.with_context(**confirm_context).action_post()
                except Exception as e:
                    request.env.cr.rollback()
                    params = {
                        'token': access_token,
                        'message': str(e)
                    }
                    return request.redirect('/autofactura/error/notify?' + werkzeug.urls.url_encode(params))
            # MAKING PAYMENTS
            try:
                inv.with_context(fast_invoicing_apply_payment=True).fast_invoicing_auto_pay()
            except Exception as e:
                request.env.cr.rollback()
                params = {
                    'token': access_token,
                    'message': str(e)
                }
                return request.redirect('/autofactura/error/notify?' + werkzeug.urls.url_encode(params))
            if inv.move_type == 'out_invoice':
                # SEND MAIL AUTOMATIC
                self._action_send_email(inv.access_token)
                url = '/autofactura/' + inv.access_token + '/' + sale_order.access_token
                params = {}
                if tpv:
                    params['tpv'] = 1
                if params:
                    url += '?%s' % werkzeug.urls.url_encode(params)
                return request.redirect(url)
        return request.redirect('/autofactura?message=no-invoice')

    @http.route('/autofactura/<string:invoice_token>/<string:order_token>',
                auth='public', website=True)
    def invoice_index(self, invoice_token, order_token, tpv=0, **kwargs):
        try:
            invoice_sudo = request.env['account.move'].with_user(SUPERUSER_ID).search([
                ('access_token', '=', invoice_token)
            ], limit=1)
        except (AccessError, MissingError):
            return request.redirect('/autofactura?message=no-token')
        if bool(tpv):
            order_sudo = request.env['pos.order'].with_user(SUPERUSER_ID).search([
                ('access_token', '=', order_token)
            ], limit=1)
        else:
            order_sudo = request.env['sale.order'].with_user(SUPERUSER_ID).search([
                ('access_token', '=', order_token)
            ], limit=1)

        if not invoice_sudo or not order_sudo:
            return request.redirect('/autofactura?message=no-token')

        return request.render('b_fast_invoicing.invoice_view', {
            'invoice': invoice_sudo,
            'order': order_sudo,
            'tpv': bool(tpv),
            'message': kwargs.get('message', '')
        })

    @http.route('/autofactura/send/<string:access_token>', auth='public', website=True)
    def send_invoice(self, access_token):
        send_message = self._action_send_email(access_token=access_token)
        if not send_message:
            return request.redirect('/autofactura?message=no-token')
        return request.redirect('/autofactura?message=' + send_message)

    def _action_send_email(self, access_token):
        inv_obj = request.env['account.move']
        invoice = inv_obj.with_user(SUPERUSER_ID).search([
            ('access_token', '=', access_token),
        ], limit=1)
        if not invoice:
            return False
        # MAKE MANUAL INVOICE SEND
        send = False
        template = request.env.ref(
            'account.email_template_edi_invoice', False).with_user(SUPERUSER_ID)
        rendering_context = dict(request.env.context)
        template = template and template.with_context(rendering_context)
        lang = request.env.context.get('lang')
        if template and template.lang:
            #lang = template._render_lang([ctx['default_res_id']])[ctx['default_res_id']]
            lang = template._render_template(template.lang, 'account.move', [invoice.id])

        invoice = invoice.with_context(lang=lang)

        if invoice.partner_id.email and template:
            mail_id = template.send_mail(invoice.id, force_send=True)
            send = bool(mail_id)

        return send and 'send-ok' or 'send-failed'

    @http.route('/autofactura/autocomplete', auth='public', website=True, type='json')
    def autocomplete_data(self, vat):
        res = {}
        partner_id = request.env['res.partner'].with_user(SUPERUSER_ID).\
            search([('vat', 'ilike', vat)], limit=1)
        if partner_id:
            res = {
                'partner': True,
                'name': partner_id.name,
                'phone': partner_id.phone,
                'email': partner_id.email,
                'l10n_mx_edi_fiscal_regime': partner_id.l10n_mx_edi_fiscal_regime,
                'vat': partner_id.vat,
                'mobile': partner_id.mobile,
                'street': partner_id.street,
                'zip': partner_id.zip,
                'city': partner_id.city,
                'state_id': partner_id.state_id.id if partner_id.state_id else '',
                'country_id': partner_id.country_id.id if partner_id.country_id else '',
                
            }
        else:
            res = {
                'partner': False,
                'name': '',
                'phone': '',
                'email': '',
                'l10n_mx_edi_fiscal_regime': '',
                'vat': '',
                'mobile': '',
                'street': '',
                'zip': '',
                'city': '',
                'state_id': '',
                'country_id': '',
            }
        return res

    @http.route('/autofactura/vat/validation', auth='public', website=True, type='json')
    def vat_validation(self, vat, country_id):
        # vat validation
        res = {}
        if not vat:
            return res
        partner_obj = request.env['res.partner']
        comp = False
        if request.env.user:
            comp = request.env.user.company_id.country_id.id
        if vat and hasattr(partner_obj, "check_vat"):
            partner_dummy = partner_obj.with_user(SUPERUSER_ID).new({
                'vat': vat,
                'name': _('Generic'),
                'country_id': (int(country_id) if country_id else comp),
            })
            try:
                partner_dummy.check_vat()
            except ValidationError as ve:
                res['error'] = ve.name or ve.value
        if not res.get('error'):
            try:
                validate(vat, validate_check_digits=True)
            except InvalidLength:
                res['error'] = _('The number has an invalid length.')
            except InvalidChecksum:
                res['error'] = _('The number"s checksum or check digit is invalid.')
            except InvalidComponent:
                res['error'] = _('One of the parts of the number are invalid or unknown.')
            except InvalidFormat:
                res['error'] = _('The number has an invalid format.')
        res['vat'] = format(vat, '')
        return res
