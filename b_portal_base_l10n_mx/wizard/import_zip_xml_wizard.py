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
    _name = "import.xml.wizard"

    filename = fields.Char("XML Filename", help="Allows you to attach only one xml or a set of compressed files in compatible formats such as .zip")
    file_xml = fields.Binary("Upload XML", required=True)

    invoice_state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled')
    ], string='Status', required=True, copy=False, tracking=True, help="State in which the invoice entered will be created or changed.")

    wizard_line_ids = fields.One2many("import.xml.wizard.line", "wizard_id")
    procesing = fields.Boolean()
    wizard_lines_show = fields.Boolean(default=False)

    def import_file(self):
        """
        CHeck the file to attach.
        If is a compressed file, uncompress and iterate over these files.
        Raises:
            ValidationError: [No file selected]
            ValidationError: [Type of file not accepted]
        Returns:
            [wizard]: same wizard with summary of files
        """
        self.remove_wizard_lines()
        self.procesing = True
        xml_tools = XmlTools()
        # File Check
        if not self.filename:
            raise ValidationError(_("No file selected"))
        zip_val = any(self.filename.lower().endswith(ext) for ext in xml_tools.COMPRESS_FORMATS)
        if not (self.filename.lower().endswith(".xml") or zip_val):
            raise ValidationError(_("File type not accepted"))
        attachment = [{'content': self.file_xml, 'fname': self.filename}]
        if zip_val:
            try:
                file_list = xml_tools.get_uncompressed_files(attachment)
            except:
                raise ValidationError(_("The file %s has been previously analyzed") % self.filename)
        else:
            file_list = attachment
        for attach in file_list:
            try:
                self.import_xml_file(attach)
            except Exception as e:
                self.create_wizard_line_create_invoice_error(attach['fname'], e)
        self.wizard_lines_show = True
        self.procesing = False
        return {
            'name': 'Summary Wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('b_portal_base_l10n_mx.b_portal_base_l10n_mx_import_xml_wizard_view_form', False).id,
            'res_model': 'import.xml.wizard',
            'res_id': self.id,
            'nodestroy': True,
            'context': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def remove_wizard_lines(self):
        # for line in self.wizard_line_ids:
        self.wizard_line_ids = False

    def import_xml_file(self, attach):
        """
        Check xml file to create or attach.
        Args:
            attach ([dict]): {fname:'file_name.xml', 'content': b'base64 file' }
        """
        filename = attach['fname']
        file_xml = attach['content']
        xml = XmlSatTools(self, file_xml, filename)
        # Check XML structure
        xml.check_xml_structure()
        # Check XML SAT (No valid states)
        xml.check_sat_status(['canceled', 'not_found'])
        # All comparations
        account_move = self.env["account.move"].search([("l10n_mx_edi_cfdi_uuid", "=", xml.get_uuid())], limit=1)
        lines_length = bool(self.env['ir.config_parameter'].sudo().get_param('activate_optional_sale_validations_line_leght'))
        lines_compare = bool(self.env['ir.config_parameter'].sudo().get_param('activate_optional_sale_validations_line'))
        if account_move:
            n_xml = account_move.get_number_xml_attached()
            if n_xml:
                self.create_wizard_line_create_invoice_error(filename,
                                                             ValidationError(_("The UUID is already used in another invoice: %s.") % account_move.name))
                return
            try:
                xml.compare_account_move(account_move, use_lines_length=lines_length, use_line_compare=lines_compare, use_realted_uuid=False)
                wizard = self.create_wizard_line_attach(filename, file_xml, account_move, is_to_create=False)
            except Exception as e:
                self.create_wizard_line_create_invoice_error(filename, ValidationError(_("The UUID is already used in another invoice")))
            return
        try:
            account_move = xml.search_account_move(use_lines_length=lines_length, use_line_compare=lines_compare)
            if account_move:
                account_move = account_move.filtered(lambda am: am.get_number_xml_attached() == 0)
        except Exception as e:
            self.create_wizard_line_create_invoice_error(filename, e)
            return
        if account_move:
            wizard = self.create_wizard_line_attach(filename, file_xml, account_move)
            # wizard.xml = xml
        else:
            try:
                response = self.env['account.move'].create_from_xml_sat(xml)
                account_move = response[0]
                account_move.write({'l10n_mx_edi_cfdi_uuid': xml.get_uuid()})
                self.create_wizard_line_validated(filename, account_move)
                body = self.get_message_chatter(xml, _("created"))
                account_move.message_post(body=body)
                self.change_state(account_move)
            except Exception as e:
                self.create_wizard_line_create_invoice_error(filename, e)

    def get_message_chatter(self, xml, action):
        """
        Create a mnessage to chatter
        Args:
            xml (XmlSatTools): XMl to extract information 
            action (str): If is attach or create
        Returns:
            [str]: message
        """
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

    def change_state(self, account_move):
        if self.invoice_state == 'draft':
            account_move.button_draft()
        if self.invoice_state == 'posted':
            # account_move.action_post()
            account_move.write({'state': self.invoice_state})
        if self.invoice_state == 'cancel':
            account_move.button_cancel()

    def compare_file_with_account_move(self, xml, account_move):
        xml.compare_length_concepts_lines(account_move.invoice_line_ids)
        xml.compare_type_xml_invoice(account_move)
        xml.compare_total_amount(account_move)
        xml.compare_concepts(account_move.invoice_line_ids)

    def create_wizard_line_validated(self, filename, account_move):
        """
         Create different type of wizzard lines
         """
        vals = {}
        message = _("Account Invoice Created Successfully.")
        self.create_wizard_line_common(vals, filename, account_move, message)
        vals['validated'] = True
        vals['is_to_attach'] = False
        vals['is_to_create'] = False
        return self.env['import.xml.wizard.line'].create(vals)

    def create_wizard_line_error(self, filename, account_move, message):
        vals = {}
        self.create_wizard_line_common(vals, filename, account_move, message)
        vals['validated'] = False
        vals['is_to_attach'] = False
        vals['is_to_create'] = False
        return self.env['import.xml.wizard.line'].create(vals)

    def create_wizard_line_create_invoice_error(self, filename, e):
        message = e.name if vars(e).get("name", False) else str(e)
        vals = {}
        vals['filename'] = filename
        vals['file_xml'] = False
        vals['wizard_id'] = self.id
        vals['account_move_id'] = False
        vals['message'] = message
        vals['validated'] = False
        vals['is_to_attach'] = False
        vals['is_to_create'] = False
        return self.env['import.xml.wizard.line'].create(vals)

    def create_wizard_line_attach(self, filename, b64_data, account_move, is_to_create=True):
        vals = {}
        message = _("Account Invoice Validated. Ready to attach")
        if is_to_create:
            message = _("Account Invoice Validated. Ready to attach or create")
        self.create_wizard_line_common(vals, filename, account_move, message)
        vals['file_xml'] = b64_data
        vals['validated'] = True
        vals['is_to_attach'] = True
        vals['is_to_create'] = is_to_create
        return self.env['import.xml.wizard.line'].create(vals)

    def create_wizard_line_common(self, vals, filename, account_move, message):
        vals['filename'] = filename
        vals['wizard_id'] = self.id
        vals['account_move_id'] = account_move.id
        vals['message'] = message
