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
    _name = "import.xml.wizard.line"

    filename = fields.Char("XML Filename")
    file_xml = fields.Binary("Upload XML", required=True)
    wizard_id = fields.Many2one("import.xml.wizard")
    account_move_id = fields.Many2one("account.move")
    account_move_name = fields.Char(related="account_move_id.name")
    message = fields.Char()
    validated = fields.Boolean()
    is_to_attach = fields.Boolean()
    is_to_create = fields.Boolean()

    def import_file_from_line(self):
        """
        Atach the xml to account move object

        Returns:
            wizard: If there are other files to attach then return a wizard otherwise close the wizard
        """
        self.env['account.move'].create_attachment_from_file(self.account_move_id, self.file_xml)
        self.wizard_id.change_state(self.account_move_id)
        self.is_to_attach = False
        # Create chatter message
        filename = self.filename
        file_xml = self.file_xml
        xml = XmlSatTools(self, file_xml, filename)
        # Update UUID
        self.account_move_id.write({'l10n_mx_edi_cfdi_uuid': xml.get_uuid()})
        body = self.wizard_id.get_message_chatter(xml, _("attached"))
        self.account_move_id.message_post(body=body)
        wizard = self.create_success_attach_wizard()
        return self.return_wizard(wizard)

    def return_wizard(self, wizard_id):
        # Close or open the wizard
        to_attach = any([wizard_line.is_to_attach for wizard_line in self.wizard_id.wizard_line_ids])
        if not to_attach:
            return {
                'name': 'Summary Wizard',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('b_portal_base_l10n_mx.b_portal_base_l10n_mx_success_info', False).id,
                'res_model': 'import.xml.wizard.info',
                'res_id': wizard_id.id,
                'nodestroy': True,
                'context': False,
                'type': 'ir.actions.act_window',
                'target': 'new',
            }
        return {
            'name': 'Summary Wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('b_portal_base_l10n_mx.b_portal_base_l10n_mx_import_xml_wizard_view_form', False).id,
            'res_model': 'import.xml.wizard',
            'res_id': self.wizard_id.id,
            'nodestroy': True,
            'context': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def create_success_create_wizard(self, title, name):
        vals = {}
        vals["title"] = title
        vals["message"] = name
        return self.env['import.xml.wizard.info'].create(vals)

    def create_success_attach_wizard(self):
        vals = {}
        vals["title"] = _("File attached successfully")
        return self.env['import.xml.wizard.info'].create(vals)

    def create_invoice_from_line(self):
        """
        Atach the xml to account move object

        Returns:
            wizard: If there are other files to attach then return a wizard otherwise close the wizard
        """
        self.is_to_attach = False
        filename = self.filename
        file_xml = self.file_xml
        xml = XmlSatTools(self, file_xml, filename)
        try:
            response = self.env['account.move'].create_from_xml_sat(xml)
            account_move = response[0]
            account_move.write({'l10n_mx_edi_cfdi_uuid': xml.get_uuid()})
            body = self.wizard_id.get_message_chatter(xml, _("created"))
            account_move.message_post(body=body)
            self.wizard_id.change_state(account_move)
            wizard = self.create_success_create_wizard(_("File created_successfully"), account_move.name)
        except Exception as e:
            mes_err = lambda e: e.name if vars(e).get("name", False) else str(e)
            self.message = mes_err(e)
            wizard = self.create_success_create_wizard(_("File create error"), self.message)
        return self.return_wizard(wizard)


class ImportXMLMessage(models.TransientModel):
    _name = "import.xml.wizard.info"

    title = fields.Char()
    message = fields.Char()
