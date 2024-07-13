# -*- encoding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.translate import _
from odoo.tools.xml_utils import _check_with_xsd

from lxml import etree, objectify
import base64
from io import BytesIO

from odoo.addons.b_portal_base_l10n_mx.models.XmlTools import XmlTools
from odoo.addons.b_portal_base_l10n_mx.models.XmlSatTools import XmlSatTools


class ImportXML(models.TransientModel):
    _name = "import.xml"

    filename = fields.Char("XML Filename")
    file_xml = fields.Binary("Upload XML", required=True, help="Only one xml file can be attached to the invoice. Otherwise it will throw an error.")

    invoice_state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled')
    ], string='Status', copy=False, tracking=True, help="State in which the invoice entered will be changed.")

    def update_account_move(self, xml, account_move):
        account_move.write({'l10n_mx_edi_cfdi_uuid': xml.get_uuid()})
        if self.invoice_state:
            if self.invoice_state == 'draft':
                account_move.button_draft()
            if self.invoice_state == 'posted':
                # account_move.action_post()
                account_move.write({'state': self.invoice_state})
            if self.invoice_state == 'cancel':
                account_move.button_cancel()
        body = self.get_message_chatter(xml, _("attached"))
        account_move.message_post(body=body)

    def get_success_wizard(self):
        return {
            'name': 'Summary',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('b_portal_base_l10n_mx.b_portal_base_l10n_mx_success_import', False).id,
            'res_model': 'import.xml',
            'res_id': self.id,
            'nodestroy': True,
            'context': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def import_file(self):
        # File Check
        if not self.filename:
            raise ValidationError(_("No file selected"))
        if not self.filename.lower().endswith(".xml"):
            raise ValidationError(_("File type not accepted"))
        xml = XmlSatTools(self, self.file_xml, self.filename)
        # Check XML structure
        xml.check_xml_structure()
        # Check XML SAT
        xml.check_sat_status(['canceled', 'not_found'])
        # All comparations
        lines_length = bool(self.env['ir.config_parameter'].sudo().get_param('activate_optional_sale_validations_line_leght'))
        lines_compare = bool(self.env['ir.config_parameter'].sudo().get_param('activate_optional_sale_validations_line'))
        account_move = self.env["account.move"].search([("l10n_mx_edi_cfdi_uuid", "=", xml.get_uuid())], limit=1)
        if account_move:
            n_xml = account_move.get_number_xml_attached()
            if n_xml:
                raise ValidationError(_("The UUID is already used in another invoice: %s") % account_move.name)
            xml.compare_account_move(account_move, use_lines_length=lines_length, use_line_compare=lines_compare, use_realted_uuid=False)
            account_move.attach_xml(self.file_xml)
            return self.get_success_wizard()
        am_id = self.env.context.get('active_id')
        account_move = self.env['account.move'].browse(am_id)
        xml.compare_account_move(account_move, use_lines_length=lines_length, use_line_compare=lines_compare)
        account_move.attach_xml(self.file_xml)
        # Update UUID
        self.update_account_move(xml, account_move)
        return self.get_success_wizard()

    def get_message_chatter(self, xml, action):
        message = ""
        message += _("<strong>The file has been successfully %s </strong> <br/>") % action
        message += "<ul>"
        message += _("<li> User: %s </li>") % self.env.user.name
        message += _("<li>Total Amount: %s </li>") % str(xml.get_amount_total())
        message += _("<li>Stamp date: %s </li>") % xml.get_stamp_date()
        message += _("<li>Serial number: %s </li>") % xml.get_serial_number()
        message += _("<li>Folio: %s </li>") % xml.get_folio()
        message += "<li>UUID: %s </li>" % xml.get_uuid()
        message += "<ul>"
        return message
