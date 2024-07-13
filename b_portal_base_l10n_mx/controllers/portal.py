# -*- encoding: utf-8 -*-
#
# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2023 Birtum - http://www.birtum.com
# All Rights Reserved.
#
# Developer(s): Carlos Maykel López González
#               (clg@birtum.com)
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

from odoo import http, _
from odoo import tools
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import ValidationError

from odoo.addons.b_portal_base_l10n_mx.models.XmlTools import XmlTools
from odoo.addons.b_portal_base_l10n_mx.models.inherit_xml_sat_tools import PortalProviderXmlSatTools

mes_err = lambda e: e.name if vars(e).get("name", False) else str(e)


class PortalProvider(CustomerPortal):
    _items_per_page = 20

    @http.route('/check_load_xml', auth='public', type='json', website=True, csrf=False)
    def check_load_xml(self, vals, **post):
        """
        Controller that handle the button add xml and create or attach a file if account invoice exist.

        Arguments:
            vals {dict} -- File uploaded and purchase order name.

        Returns:
            dict -- Successfull or message error.
        """
        data = vals.get('data', False)
        p_id = vals.get('order_id', False)
        filename = vals.get('fname', "")
        xml_tools = XmlTools()
        zip_val = any(filename.lower().endswith(ext) for ext in xml_tools.COMPRESS_FORMATS)
        if not (filename.lower().endswith(".xml") or zip_val):
            return [{'header': 'Error', 'message': _("File type not accepted"), 'name': filename, 'code': 0}]
        attachment = [{'content': data.split(',')[1].encode("utf-8"), 'fname': filename}]
        if zip_val:
            try:
                file_list = xml_tools.get_uncompressed_files(attachment)
            except:
                return [{'header': 'Error', 'message': _("The file %s has been previously analyzed") % filename, 'name': filename, 'code': 0}]
        else:
            file_list = attachment
        response = []
        for attach in file_list:
            try:
                response.append(self.process_xml(attach['content'], p_id, attach['fname']))
            except Exception as e:
                response.append({'header': 'Error', 'message': mes_err(e), 'name': attach['fname'], 'code': 0})
        print(response)
        return response

    def process_xml(self, data, p_id, filename):
        """
        Process XML
        Args:
            data (b64): File data in base 64
            p_id (int): Id from purchase order
            filename (str): Filename.

        Raises:
            ValidationError: Si no hay un archivo o una ordern.
            ValidationError: Si no hay una orden con el id.
            ValidationError: Si el tipo de archivo no es xml.

        Returns:
            dict: response
        """
        if not data or not p_id:
            raise ValidationError(_('No file'))
        p_order = request.env['purchase.order'].sudo().search([('id', '=', int(p_id))])
        if not p_order:
            raise ValidationError(_('Purchase Order Not Found'))
        if not filename.lower().endswith(".xml"):
            raise ValidationError(_('File type not accepted'))
        partner = request.env.user
        n_invoice = p_order.invoice_count

        # XML Check
        xml = PortalProviderXmlSatTools(p_order, data, filename)
        # Check XML structure
        xml.check_xml_structure()

        # Check XML SAT
        xml.check_sat_status(['canceled', 'not_found'])

        # All comparations
        lines_length = bool(request.env['ir.config_parameter'].sudo().get_param('activate_optional_sale_validations_line_leght'))
        lines_compare = bool(request.env['ir.config_parameter'].sudo().get_param('activate_optional_sale_validations_line'))
        account_move = request.env["account.move"].sudo().search([("l10n_mx_edi_cfdi_uuid", "=", xml.get_uuid())], limit=1)
        xml.check_valid_vat(p_order)
        # Verifica si el xml con el UUID asociado tiene xml y si corresponde con el xml a adjuntar.
        if account_move:
            return self.handle_account_move(account_move, xml, filename, lines_length, lines_compare)
        # Verifica si alguna de las facturas asociadas al pedido tiene un xml y si no, verifica si coincide.
        if n_invoice:
            response = self.handle_purchase_invoice(p_order, xml, filename, lines_length, lines_compare)
            if response:
                return response
        # Crea la factura a partir del xml.
        (new_invoice, attachment) = self.create_invoice(p_order, xml)
        self.link_po_invoice(new_invoice, p_order)
        self.update_status(new_invoice, xml)
        response = {'header': 'Success', 'message': _("The Account Invoice %s was created succesfully.") % new_invoice.name, 'name': filename, 'code': 2}
        return response

    def create_invoice(self, p_order, xml):
        """
        Create invoice from xml and check purchase from xml.

        Args:
            p_order (purchase.order): Purchase Order
            xml (XMLSatTools): xml.

        Returns:
            dict: response
        """
        xml.check_purchase_invoice(p_order)
        response = request.env['account.move'].sudo().create_from_xml_sat(xml)
        return response

    def link_po_invoice(self, account_move, purchase_order):
        """
        Link the account move to purchase order.

        Args:
            account_move (account.move): Account Move
            purchase_order (purchase.order): Purchase order to link
        """
        previous_ids = [invoice.id for invoice in purchase_order.invoice_ids]
        previous_ids.append(account_move.id)
        purchase_order.write({'invoice_ids': [(6, 0, previous_ids)]})
        po_lines = purchase_order.order_line
        for line in account_move.line_ids:
            am_product = line.product_id.id
            po_line = po_lines.filtered(lambda p: p.product_id.id == am_product)
            po_dict = {'purchase_order_id': purchase_order.id, 'purchase_line_id': po_line.id}
            line.write(po_dict)

    def handle_account_move(self, account_move, xml, filename, lines_length, lines_compare):
        """
        Check if account move is related to xml.

        Args:
            account_move (account.move): Account Move to check
            xml (XMLSATools): xml.
            filename (str): Filename
            lines_length (bool): optional check.
            lines_compare (bool): optional check.

        Returns:
            dict: Response
        """
        n_xml = account_move.get_number_xml_attached()
        if n_xml:
            message = _("The UUID is already used in another invoice: %s") % account_move.name
            return {'header': 'Error', 'message': message, 'name': filename, 'code': 0}
        message_return = {'header': 'Error', 'message': "", 'name': filename, 'code': 0}
        try:
            xml.compare_account_move(account_move, use_lines_length=lines_length, use_line_compare=lines_compare, use_realted_uuid=False)
            account_move.attach_xml(xml.b64_file)
            message_return = {'header': 'Success', 'message': _("The file was attached successfully"), 'name': filename, 'code': 2}
        except Exception as e:
            message_return = {'header': 'Error', 'message': mes_err(e), 'name': filename, 'code': 0}
        return message_return

    def handle_purchase_invoice(self, purchase_order, xml, filename, lines_length, lines_compare):
        """
        Check all invoices from purchase order.

        Args:
            purchase_order (purchase.order): Purchase Order
            xml (XMLSATools): xml.
            filename (str): Filename
            lines_length (bool): optional check.
            lines_compare (bool): optional check.

        Returns:
            dict: Response
        """
        for invoice in purchase_order.invoice_ids:
            if not invoice.get_number_xml_attached():
                try:
                    xml.compare_account_move(invoice, use_lines_length=lines_length, use_line_compare=lines_compare, use_realted_uuid=False)
                    invoice.attach_xml(xml.b64_file)
                    self.update_status(invoice, xml)
                    message_return = {'header': 'Success', 'message': _("The file was attached successfully to %s") % invoice.name, 'name': filename, 'code': 2}
                    return message_return
                except Exception as e:
                    print(e)
                    continue
        return False

    def update_status(self, account_move, xml):
        """
        Update de invoice status.

        Args:
            account_move (account.move): Account Move to update.
            xml (XMLSATools): xml.
        """
        invoice_state = request.env['ir.config_parameter'].sudo().get_param('portal_xml_state')
        account_move.write({'l10n_mx_edi_cfdi_uuid': xml.get_uuid()})
        if invoice_state == 'draft':
            account_move.button_draft()
        if invoice_state == 'posted':
            account_move.write({'state': invoice_state})
        if invoice_state == 'cancel':
            account_move.button_cancel()
