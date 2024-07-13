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

from odoo import SUPERUSER_ID, _, http
from odoo.exceptions import AccessError, MissingError, UserError, ValidationError
from odoo.http import request

import werkzeug
import werkzeug.urls

logger = logging.getLogger(__name__)


class FastInvoicing(http.Controller):

    @http.route('/autofactura/error/notify', auth='public', website=True)
    def invoice_notify_error(self, **kwargs):
        sale_order = request.env['sale.order'].with_user(SUPERUSER_ID).search([
            ('access_token', '=', kwargs.get('token', 'n/d'))
        ], limit=1)
        sale_order.fi_action_send_error(kwargs.get('message', ''))
        return request.redirect('/autofactura/error/{}'.format(sale_order.access_token))

    @http.route('/autofactura/error/<string:access_token>', auth='public', website=True)
    def invoice_error(self, access_token, **kwargs):
        sale_order = request.env['sale.order'].with_user(SUPERUSER_ID).search([
            ('access_token', '=', access_token)
        ], limit=1)
        return request.render('b_fast_invoicing.invoice_error', {
            'order': sale_order
        })

    @http.route('/autofactura/search', auth='public', website=True, type='json')
    def search_order(self, search=''):
        # TODO: Domain more complex
        order = request.env['sale.order'].with_user(SUPERUSER_ID).search([
            ('invoicing_ref', '=', search),
        ], limit=1)
        order.write({'access_token': str(uuid.uuid4())})
        return {
            'access_token': order.access_token,
            'search': search,
            'is_pos': False
        }
    @http.route(['/autofactura/pedido/<string:access_token>',
                 '/autofactura/pedido/<string:vat>/<string:access_token>'], auth='public', website=True)
    def order_index(self, access_token, vat=False, **kwargs):
        order = request.env['sale.order'].with_user(SUPERUSER_ID).search([
            ('access_token', '=', access_token)
        ], limit=1)
        inv = False
        if vat:
            partner = request.env['res.partner'].with_user(SUPERUSER_ID).search([
                ('vat', '=', vat)], limit=1)
        else:
            partner = False
        go_url = '#'
        if order.invoice_status == 'invoiced':
            inv = order.invoice_ids.filtered(
                lambda x: x.state != 'cancel' and x.move_type == 'out_invoice')[:1]
            if inv and inv.access_token:
                go_url = '/autofactura/' + inv.access_token + '/' + order.access_token

        return request.render('b_fast_invoicing.invoicing_order_page', {
            'order': order,
            'search': '',
            'go_url': go_url,
            'invoice': inv,
            'vat_cont': vat if vat else '',
            'partner': partner if partner else False,
            'is_pos': False,
            'cfdi': self.get_cfdi_usage(),
        })

    @http.route('/autofactura/pedido/search/<string:search>', auth='public', website=True)
    def no_order_index(self, search=False, **kwargs):
        return request.render('b_fast_invoicing.invoicing_order_page', {
            'order': False,
            'search': search,
            'is_pos': False,
            'invoice': False
        })

    @http.route(['/autofactura/invoicing/<string:access_token>',
                 '/autofactura/invoicing/<string:vat>/<string:access_token>'], auth='public', website=True)
    def invoicing_index(self, access_token, vat=False, **post):
        order = request.env['sale.order'].with_user(SUPERUSER_ID).search([
            ('access_token', '=', access_token)
        ])
        partner = order.partner_id
        p_rfc = partner.vat
        vats = []
        if p_rfc:
            vats = [(p_rfc, p_rfc)] + [(partner.vat, partner.vat)]
        return request.render('b_fast_invoicing.invoicing_invoicing_modal', {
            'order': order,
            'partner': order.partner_id,
            'tpv': 0,
            'vat': vat if vat else '',
            'cfdi_use': post.get('cfdi_use'),
            'cfdi': self.get_cfdi_usage(),
            'payment_method': self.get_payment_method(),
            'l10n_mx_edi_fiscal_regime': self.get_l10n_mx_edi_fiscal_regime(),
            'vats': vats
        })

    def get_payment_method(self):
        val = []
        for r in request.env['l10n_mx_edi.payment.method'].with_user(SUPERUSER_ID).search([]):
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
        


    @http.route('/autofactura/message/post', auth='public', website=True, type='json')
    def fi_message_post(self, order_id, message):
        sale_order = request.env['sale.order'].with_user(SUPERUSER_ID).search([
            ('access_token', '=', order_id)
        ], limit=1)
        if sale_order:
            body = _('<p>Message from auto invoice by {}</p>').format(sale_order.partner_id.name)
            if message:
                body += message
            sale_order.message_post(body=body)
        return True

