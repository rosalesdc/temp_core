# -*- encoding: utf-8 -*-
#
# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2023 Birtum - https://www.birtum.com
# All Rights Reserved.
#
# Developer(s): Alan Guzmán
#               age@wedoo.tech
#######################################################################
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
#######################################################################
from odoo import http
from odoo import exceptions, SUPERUSER_ID
from odoo.http import request
from odoo.tools.float_utils import float_compare
from odoo.tools import consteq


class PortalStockPiking(http.Controller):

    @http.route('/create_invoice', auth='public', type='json', website=True, csrf=False)
    def create_invoice_from_js(self, vals, **post):
        """
            Controller that handle the button add xml and create or attach a file if account invoice exist.
            Arguments:
                vals {dict} -- File uploaded and purchase order name.
            Returns:
                dict -- Successfull or message error.
        """
        pid = vals['pid']
        picking_obj = request.env['stock.picking'].sudo()
        # TODO
        # picking has to be arrive in vals from frontend
        picking = vals.get('picking', False)
        if not picking:
            return {'message': 'Error: No se encontro la recepción', 'success': False}
        check_invoiced = picking_obj.check_invoiced(int(picking))
        if check_invoiced.get('invoiced', False):
            return {'message': 'Error: La recepción ha sido previamente facturada', 'success': False}
        picking_id = picking_obj.browse(int(picking))
        purchase_line_ids = picking_id.move_ids.filtered(lambda x: x.purchase_line_id and not x.purchase_line_id.display_type).mapped('purchase_line_id')
        if not purchase_line_ids:
            return {'message': 'Error: No hay lineas de compra por facturar', 'success': False}
        precision = request.env['decimal.precision'].sudo().precision_get('Product Unit of Measure')
        if all(
                float_compare(
                    line.qty_invoiced,
                    line.product_qty if line.product_id.purchase_method == "purchase" else line.qty_received,
                    precision_digits=precision,
                ) >= 0 for line in purchase_line_ids):
            return {'message': 'Error: No hay lineas facturables para esta recepción', 'success': False}
        invoiceble_lines = [p_line for p_line in purchase_line_ids if self._check_purchase_line_to_invoice(p_line)]
        if len(invoiceble_lines) <= 0:
            return {'message': 'Error: No hay lineas facturables para esta recepción', 'success': False}
        order = request.env['purchase.order'].sudo().browse(int(pid))

        invoice_id = order.sudo().action_portal_create_invoice()

        msg = 'Info: Factura creada con éxito: '
        if invoice_id.state == 'draft':
            msg += 'Borrador de factura (*{})'.format(invoice_id.id)
        else:
            msg += invoice_id.name
        return {'res_id': invoice_id.id, 'success': True, 'message': msg}

    def _check_purchase_line_to_invoice(self, purchase_line):
        """
            tool metho that helps to know if a purchase order line can be invoiced
            :receive: purachase_line: a record of purchase.order.line
            :return: returns the qty to be invoiced.
        """
        qty = 0.0
        if purchase_line.product_id.purchase_method == 'purchase':
            qty = purchase_line.product_qty - purchase_line.qty_invoiced
        else:
            qty = purchase_line.qty_received - purchase_line.qty_invoiced
        return qty

    @http.route('/invoice_load_pdf', auth='public', type='json', website=True, csrf=False)
    def invoice_load_pdf(self, vals, **post):
        """
        Controller that handle the button add pdf and create or attach a file if account invoice exist.
        Arguments:
            vals {dict} -- File uploaded and 'invoice_id'.
        Returns:
            dict -- Successfull or message error.
        """
        invoice_obj = request.env['account.move'].sudo()
        try:
            invoice_id = invoice_obj.browse(int(vals.get('invoice_id')))
            fname = vals['fname']
            content = vals['data'].split(',')[1]
            content = content.encode('utf-8')
        except Exception as e:
            print(e)
            return {'message': 'Error: Hubo un error al momento de procesar el PDF', 'success': False}
        ok_pdf = self._attach_pdf_to_invoice(invoice_id.id, fname, content)
        if ok_pdf != True:
            return ok_pdf
        if invoice_id.name != '/':
            msg = 'El PDF ha sido adjuntado exitosamente a la factura %s' % invoice_id.name
        else:
            msg = 'El PDF ha sido adjuntado exitosamente al borrador de factura (*%s)' % invoice_id.id
        return {'message': msg, 'success': True}

    def _attach_pdf_to_invoice(self, invoice_id, fname, content):
        """
            tool method that creates a new record of a pdf at ir.attachment
            :receive: invoice_id: the selected invoice at portal provider, it is used to attach the pdf file.
            :receice: pdf: The pdf sent from portal provider to back, it is used to create the attachment.
            :returns: return a dict message error or True.
        """
        try:
            request.env['ir.attachment'].sudo().create(
                {
                    'name': fname,  # filename
                    'datas': content,  # base64 string
                    'res_model': 'account.move',
                    'description': 'PDF Importado desde el portal de proveedores',
                    'res_id': invoice_id,
                })
        except Exception as e:
            print(e)
            return {'message': 'Error: Hubo un error al momento de procesar el PDF', 'success': False}
        return True

    def _stock_picking_check_access(self, picking_id, access_token=None):
        picking = request.env['stock.picking'].browse(int(picking_id))
        picking_sudo = picking.sudo()
        try:
            picking.check_access_rights('read')
            picking.check_access_rule('read')
        except exceptions.AccessError:
            if not access_token or not consteq(picking_sudo.sale_id.access_token, access_token):
                raise
        return picking_sudo

    @http.route(['/my/purchase/print/<pid>/'], type='http', auth="user", website=False)
    def print_delivery_slip(self, pid, access_token=None, **kwargs):
        """
            Controller that handle the button download slip.
            Arguments:
                vals {dict} -- 'picking_id'.
            Returns:
                dict -- Successfull downloaded PDF or message error.
        """
        picking_obj = request.env['stock.picking'].sudo()
        try:
            picking_sudo = self._stock_picking_check_access(pid, access_token=access_token)
            picking_id = picking_obj.browse(int(pid))
        except Exception as e:
            print(e)
            return request.redirect('/my/purchase')

        pdf = request.env['ir.actions.report'].sudo()._render_qweb_pdf('stock.action_report_delivery', [picking_sudo.id])[0]
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)
