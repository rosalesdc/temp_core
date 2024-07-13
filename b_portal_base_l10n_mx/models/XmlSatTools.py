# -*- encoding: utf-8 -*-

import base64
import datetime
import requests
from lxml import etree, objectify
from lxml.objectify import fromstring
from io import BytesIO, StringIO
from . import XmlTools

from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Date
from odoo.addons import decimal_precision as dp
from odoo.tools.xml_utils import _check_with_xsd

CFDI_SAT_QR_STATE = {
    'No Encontrado': 'not_found',
    'Cancelado': 'cancelled',
    'Vigente': 'valid',
}


class XmlSatTools:
    odoo_obj = object()
    b64_file = bytes()
    xml_pairs = object()
    xml_dict = object()

    concepts_invoice_line = []
    xml_type = str()
    odoo__line_fields_compare = [['product_id.default_code', 'product_id.unspsc_code_id.code'], 'quantity', 'price_unit']
    xml_concept_fields_compare = [[['@NoIdentificacion'], ['@ClaveProdServ']], ['@Cantidad'], ['@ValorUnitario']]

    optional_fields = []

    error_message = ""

    def __init__(self, odoo_obj, b64_file, filename):
        self.odoo_obj = odoo_obj
        self.b64_file = b64_file
        attachment = [{'content': b64_file, 'fname': filename}]
        xml_tools = XmlTools.XmlTools()
        self.xml_pairs = xml_tools._get_xml_pairs(attachment)
        self.xml_dict = self.xml_pairs[0][0]
        self.get_get_type_of_invoice(odoo_obj.env.company.vat)
        self.default_concept_map = {
            '@NoIdentificacion': "default_code", '@ClaveProdServ': "sat_code",
            '@ValorUnitario': "price_unit", '@Cantidad': "quantity", '@Descuento': "discount",
            '@Importe': "total", '@ClaveUnidad': "unit_code", "@Unidad": "type", '@Descripcion': "description"
        }

        self.default_tax_map = {
            "@Base": "base", "@Impuesto": "sat_tax_code", "@TipoFactor": "factor",
            "@TasaOCuota": "amount", "@Importe": "importe"
        }

    def search_account_move(self, use_lines_length=False, use_line_compare=True):
        """
        Search any account invoice with the same fields that xml.

        Raises:
            ValidationError: If multiple invoices have the same UUID

        Returns:
            [account.move]: Account Move
        """
        am = self.get_related_account_move()
        if am and len(am) > 1:
            raise ValidationError(_("Multiple invoices have the same UUID"))
        if am:
            self.check_account_move(am)
            return am
        domain = []
        # Search by partner
        partner = self.search_partner()[0]
        domain.append(('partner_id', '=', partner.id))
        # Search by payment term
        payment_term = self.search_payment_term()
        if payment_term:
            domain.append(('invoice_payment_term_id', '=', payment_term.id))
        # Search by Total
        total = self.get_amount_total()
        domain.append(('amount_total', '=', total))
        # Search by Subtotal
        sub = self.get_amount_subtotal()
        domain.append(('amount_untaxed', '=', sub))
        # Search by type
        am_type = self.search_by_type()
        domain.append(('move_type', 'in', am_type))
        ams = self.odoo_obj.env['account.move'].search(domain)
        if not ams:
            return False
        if type(ams) != type(list()) and len(ams) <= 1:
            ams = [ams]
        for am in ams:
            try:
                self.compare_account_move(am, use_lines_length=use_lines_length, use_line_compare=use_line_compare)
                return am
            except:
                continue
        return False

    def check_account_move(self, am):
        try:
            self.check_partner(am)
        except Exception as e:
            self.error_message += str(e) + "\n"
        try:
            self.compare_length_concepts_lines(am.invoice_line_ids)
        except Exception as e:
            self.error_message += str(e) + "\n"
        try:
            self.compare_type_xml_invoice(am)
        except Exception as e:
            self.error_message += str(e) + "\n"
        try:
            self.compare_total_amount(am)
        except Exception as e:
            self.error_message += str(e) + "\n"
        try:
            self.compare_concepts(am.invoice_line_ids)
        except Exception as e:
            self.error_message += str(e) + "\n"
        if self.error_message != "":
            raise ValidationError(self.error_message)

    def search_by_type(self):
        """
        Return a list of type for invoice search

        Returns:
            [list]: invoice type
        """
        if self.xml_type == 'is_client':
            return ['out_invoice', 'out_refund', 'out_receipt']
        else:
            return ['in_invoice', 'in_refund', 'in_receipt']

    def search_payment_term(self):
        """
        Search payment term object.

        Returns:
            [account.payment.term]: Payment term
        """
        payment_term = self.get_payment_term()
        if payment_term == "":
            return False
        pm = self.odoo_obj.env['account.payment.term'].search([('name', 'like', payment_term)])
        return pm

    def search_partner(self):
        """
        Search a partner to match

        Raises:
            ValidationError: If any vat in xml doesnt match with the odoo partner
            ValidationError: Partner not found
            ValidationError: Partners with the same Vat

        Returns:
            [res.partner]: REs partner mathed
        """
        env = self.odoo_obj.env['res.partner']
        vat = ""
        if self.xml_type == 'is_client':
            vat = self.get_customer_vat()
        elif self.xml_type == 'is_provider':
            vat = self.get_supplier_vat()
        else:
            raise ValidationError(_("Unknown type of invoice"))
        partner = env.search([('vat', '=', vat)])
        if not partner:
            raise ValidationError(_("Partner not found with VAT: %s") % vat)
        """
        if len(partner)>1:
            raise ValidationError(_("Multiple Partners with VAT: %s") % vat)
        """
        return partner

    def compare_vat_suplier(self, partner_vat):
        return partner_vat == self.get_supplier_vat()

    def compare_vat_customer(self, partner_vat):
        return partner_vat == self.get_customer_vat()

    def get_get_type_of_invoice(self, partner_vat):
        """
        Assing the type of invoice to a field in class

        Args:
            partner_vat (str): Vat of partner

        Returns:
            [str]: Type of invoice
        """
        self.xml_type = self._get_type_of_invoice(partner_vat)
        return self.xml_type

    def _get_type_of_invoice(self, partner_vat):
        """
        Return the type of invoice 

        Args:
            partner_vat (str): Vat of partner

        Returns:
            [str]: Type of invoice
        """
        if self.compare_vat_suplier(partner_vat):
            return 'is_client'
        if self.compare_vat_customer(partner_vat):
            return 'is_provider'
        return 'unknown'

    def get_odoo_field(self, odoo_obj, fields_list):
        """
        Return the odoo field value, it's recursive because support
        fields like account_move.partner_id.vat
        Args:
            odoo_obj (odoo.object): object to start the search
            fields_list (list): list of fields (separated by '.')

        Raises:
            ValidationError: If any intermediate object is a list

        Returns:
            obj: The value of field
        """
        if len(odoo_obj) > 1:
            raise ValidationError(_("Error: expected singleton"))
        if type(fields_list) == type(str()):
            return getattr(odoo_obj, fields_list)
        if len(fields_list) == 1:
            return getattr(odoo_obj, fields_list[0])
        new_data = getattr(odoo_obj, fields_list[0])
        return self.get_odoo_field(new_data, fields_list[1:])

    def compare_multi_fields(self, am_line, xml_concept, odoo_fields, xml_fields):
        """
        Compare an return multiple fields.
        If it is not known with certainty with which field it is necessary to compare, 
        the comparison is made with several fields hoping that one of them matches.

        Args:
            am_line (account.move.line): line to iniciate the search
            xml_concept (OrderedDict): xml concept
            odoo_fields (list): Fields to search in odoo obj
            xml_fields (list): FIelds to search in xml dict
            
        Raises:
            ValidationError: If the fields are inconsistent, for example ['product'] != product
            ValidationError: If in the search any error ocurred, then catch the error.

        Returns:
            [type]: [description]
        """
        if len(odoo_fields) != len(xml_fields):
            raise ValidationError(_("The fields to compare are inconsistent"))
        bool_result = False
        for i in range(len(odoo_fields)):
            try:
                odoo_field_value = self.get_odoo_field(am_line, odoo_fields[i].split('.'))
            except Exception as e:
                raise ValidationError(_("Internal Error: %s") % e)
            xml_field_value = self.dict_unsensitive_search(xml_concept, xml_fields[i].copy())
            bool_result = bool_result or (str(odoo_field_value) == str(xml_field_value))
            if bool_result:
                self.optional_fields.append((odoo_fields[i], xml_fields[i]))
        return bool_result

    def compare_field(self, am_line, xml_concept, odoo_field, xml_field):
        """
        Compare the field in xml_dict vs odoo obj

        Args:
            am_line (account.move.line): line to iniciate the search
            xml_concept (OrderedDict): xml concept
            odoo_fields (list): Fields to search in odoo obj
            xml_fields (list): FIelds to search in xml dict

        Returns:
            [bool]: if match or no
        """
        odoo_f = self.get_odoo_field(am_line, odoo_field)
        xml_f = self.dict_unsensitive_search(xml_concept, xml_field.copy())
        if type(odoo_f) == type(float()):
            return odoo_f == float(xml_f)
        return str(odoo_f) == str(xml_f)

    def compare_concept(self, concept, invoice_lines):
        """
        Compare concept to invoice_lines

        Args:
            concept (OrderedDict): concept to compare
            invoice_lines (odoo.obj.list): invoice lines

        Raises:
            ValidationError: If type of fields are not the same

        Returns:
            bool,account_move_line: Invoice line
        """
        if self.xml_type == "is_client":
            return self.compare_concept_lines(concept, invoice_lines, self.odoo__line_fields_compare, self.xml_concept_fields_compare)
        else:
            return self.compare_concept_lines_purchase(concept, invoice_lines)

    def compare_concept_lines_purchase(self, concept, invoice_lines):
        self.odoo_obj.env["account.move"].check_extra_module()
        odoo__line_fields_compare = ['quantity', 'price_unit']
        xml_concept_fields_compare = [['@Cantidad'], ['@ValorUnitario']]
        values = self.compare_concept_lines(concept, invoice_lines, odoo__line_fields_compare, xml_concept_fields_compare)
        if not values:
            return values
        values = [value for value in values]
        product = self.compare_concept_line_purchase_product(concept, values)
        return product

    def compare_concept_line_purchase_product(self, concept, invoice_lines):
        n_invoice = 0
        for am_line in invoice_lines:
            product_sku = concept['@NoIdentificacion']
            valid = False
            for seller_id in am_line.product_id.provider_ids:
                if seller_id.product_sku == product_sku:
                    valid = True
                    break
            if valid:
                return invoice_lines.pop(n_invoice)
            n_invoice += 1
        return False

    def compare_concept_lines(self, concept, invoice_lines, odoo__line_fields_compare, xml_concept_fields_compare):
        n_invoice = 0
        for am_line in invoice_lines:
            concept_valid = True
            for k in range(len(odoo__line_fields_compare)):
                odoo_field = odoo__line_fields_compare[k]
                xml_field = xml_concept_fields_compare[k]
                if type(odoo_field) == type(xml_field[0]):
                    if type(odoo_field) == type(list()):
                        valid = self.compare_multi_fields(am_line, concept, odoo_field, xml_field)
                    else:
                        valid = self.compare_field(am_line, concept, odoo_field, xml_field)
                    concept_valid = concept_valid and valid
                else:
                    raise ValidationError(_("Internal Error: Non equal comparation type in compare concept"))
            if concept_valid:
                return invoice_lines.pop(n_invoice)
            n_invoice += 1
        return False

    def compare_concepts(self, am_lines):
        """
        Iterate over concepts to find any account_move line with the same data

        Args:
            am_lines (account.move.line): Lines to compare

        Raises:
            ValidationError: If no line matches the concept
        """
        list_concepts = self.get_concepts()
        invoice_lines = [line for line in am_lines]
        for concept in list_concepts:
            invoice_line_match = self.compare_concept(concept, invoice_lines)
            if not invoice_line_match:
                raise ValidationError(_("The xml does not match the invoice"))
            else:
                self.concepts_invoice_line.append((concept, invoice_line_match))

    def compare_type_xml_invoice(self, account_move):
        if account_move.move_type in ['out_invoice', 'out_refund', 'out_receipt'] and self.xml_type != 'is_client':
            raise ValidationError(_("Type of invoice ' %s ' doesn't match with the xml.") % account_move.move_type)
        elif account_move.move_type in ['in_invoice', 'in_refund', 'in_receipt'] and self.xml_type != 'is_provider':
            raise ValidationError(_("Type of invoice ' %s ' doesn't match with the xml.") % account_move.move_type)

    def compare_total_amount(self, account_move):
        xml_amount = self.get_amount_total()
        if account_move.amount_total != float(xml_amount):
            str_diff = "{} != {} .".format(account_move.amount_total, xml_amount)
            raise ValidationError(_("Amount of invoice doesn't match with the xml amount %s.") % str_diff)

    def compare_length_concepts_lines(self, invoice_lines):
        invoice_line_len = len(invoice_lines)
        concepts_len = len(self.get_concepts())
        if invoice_line_len != concepts_len:
            len_str = "{} != {} .".format(invoice_line_len, concepts_len)
            raise ValidationError(_("Length of invoice lines doesn't match with length of xml concepts %s.") % len_str)

    def check_related_uuid(self):
        invoice = self.odoo_obj.env['account.move'].search([('l10n_mx_edi_cfdi_uuid', '=', self.get_uuid())])
        if invoice:
            raise ValidationError(_("The UUID is related to another invoice %s") % invoice.name)

    def get_related_account_move(self):
        return self.odoo_obj.env['account.move'].search([('l10n_mx_edi_cfdi_uuid', '=', self.get_uuid())])

    def check_partner(self, account_move):
        partner_error = ValidationError(_("The partner related to the invoice does not correspond to the one on the invoice."))
        if self.xml_type == 'is_client' and not account_move.partner_id.vat == self.get_customer_vat():
            raise partner_error
        if self.xml_type == 'is_provider' and not account_move.partner_id.vat == self.get_supplier_vat():
            raise partner_error
        if self.xml_type == 'unknown':
            raise ValidationError(_("Unknown type of invoice, no vat correspond to those registered in the system"))

    def compare_account_move_concepts(self, account_move):
        mes_err = lambda e: e.name if vars(e).get("name", False) else str(e)
        try:
            self.compare_concepts(account_move.invoice_line_ids)
        except Exception as e:
            self.error_message += mes_err(e) + "\n"

    def check_length_concepts(self, account_move):
        mes_err = lambda e: e.name if vars(e).get("name", False) else str(e)
        try:
            self.compare_length_concepts_lines(account_move.invoice_line_ids)
        except Exception as e:
            self.error_message += mes_err(e) + "\n"

    def compare_account_move(self, account_move, use_lines_length=False, use_line_compare=True, use_realted_uuid=True):
        mes_err = lambda e: e.name if vars(e).get("name", False) else str(e)
        if use_realted_uuid:
            try:
                self.check_related_uuid()
            except Exception as e:
                self.error_message += mes_err(e) + "\n"
        try:
            self.check_partner(account_move)
        except Exception as e:
            self.error_message += mes_err(e) + "\n"
        try:
            self.compare_type_xml_invoice(account_move)
        except Exception as e:
            self.error_message += mes_err(e) + "\n"
        try:
            self.compare_total_amount(account_move)
        except Exception as e:
            self.error_message += mes_err(e) + "\n"
        # Optional validations
        if use_lines_length:
            self.check_length_concepts(account_move)
        if use_line_compare:
            self.compare_account_move_concepts(account_move)
        if self.error_message != "":
            raise ValidationError(self.error_message)
        return True

    def get_date(self):
        return self.dict_unsensitive_search(self.xml_dict, ['cfdi:Comprobante', '@Fecha'])

    def get_folio(self):
        return self.dict_unsensitive_search(self.xml_dict, ['cfdi:Comprobante', '@Folio'])

    def get_serial_number(self):
        return self.dict_unsensitive_search(self.xml_dict, ['cfdi:Comprobante', '@Serie'])

    def get_stamp_date(self):
        return self.dict_unsensitive_search(self.xml_dict, ['cfdi:Comprobante', 'cfdi:Complemento', 'tfd:TimbreFiscalDigital', '@FechaTimbrado'])

    def get_uuid(self):
        return self.dict_unsensitive_search(self.xml_dict, ['cfdi:Comprobante', 'cfdi:Complemento', 'tfd:TimbreFiscalDigital', '@UUID'])

    def get_supplier_vat(self):
        return self.dict_unsensitive_search(self.xml_dict, ['cfdi:Comprobante', 'cfdi:Emisor', '@Rfc'])

    def get_customer_vat(self):
        return self.dict_unsensitive_search(self.xml_dict, ['cfdi:Comprobante', 'cfdi:Receptor', '@Rfc'])

    def get_amount_total(self):
        return float(self.dict_unsensitive_search(self.xml_dict, ['cfdi:Comprobante', '@Total']))

    def get_concepts(self):
        concepts = self.dict_unsensitive_search(self.xml_dict, ['cfdi:Comprobante', 'cfdi:Conceptos', 'cfdi:Concepto'])
        if type(concepts) != type(list()):
            return [concepts]
        return concepts

    def get_supplier_name(self):
        return self.dict_unsensitive_search(self.xml_dict, ['cfdi:Comprobante', 'cfdi:Emisor', '@Nombre'])

    def get_local_taxes(self):
        return self.dict_unsensitive_search(self.xml_dict, ['cfdi:Comprobante', 'cfdi:Complemento', 'implocal:ImpuestosLocales'])

    def get_amount_subtotal(self):
        return float(self.dict_unsensitive_search(self.xml_dict, ['cfdi:Comprobante', '@SubTotal']))

    def get_payment_term(self):
        return self.dict_unsensitive_search(self.xml_dict, ['cfdi:Comprobante', '@CondicionesDePago'])

    def get_payment_form(self):
        return self.search(self.xml_dict, ['cfdi:Comprobante', '@FormaPago'])

    def get_cfdi_use(self):
        return self.search(self.xml_dict, ['cfdi:Comprobante', 'cfdi:Receptor', '@UsoCFDI'])

    def get_payment_method(self):
        return self.search(self.xml_dict, ['cfdi:Comprobante', '@MetodoPago'])

    def check_sat_status(self, not_valid_states):
        status = self.get_sat_status()
        if type(status) == type(dict()):
            raise ValidationError(_("Error Validating SAT status %s") % status['error'])
        if status in not_valid_states:
            raise ValidationError(_("XML not found in SAT"))

    def search(self, search_dict, keys, default=''):
        search = self.dict_unsensitive_search(search_dict, keys)
        if search == '':
            return default
        return search

    def check_tax_consecuent(self, concept):
        taxes = self.get_concept_taxes(concept)
        amount = float(self.search(concept, ['@Importe']))
        for tax in taxes:
            base_tax = self.search(tax, ['@Base'])
            equal = (amount == self.search(tax, ['@Base']))
            if not equal:
                return equal
            amount = amount + base_tax
        return True

    def get_concept_taxes(self, concept):
        taxes = self.dict_unsensitive_search(concept, ['cfdi:Impuestos', 'cfdi:Traslados', 'cfdi:Traslado'])
        if type(taxes) != type(list()):
            taxes = [taxes]
        return taxes

    def get_concept_dict(self, concept, values_map=False):
        values_map = values_map if values_map else self.default_concept_map
        return self.map_dict(concept, values_map)

    def map_dict(self, dict_it, dict_map):
        maped_dict = {}
        for key in dict_it.keys():
            if dict_map.get(key, False):
                maped_dict[dict_map.get(key)] = self.search(dict_it, [key])
            else:
                maped_dict[key] = self.search(dict_it, [key])
        return maped_dict

    def get_tax_dict(self, tax_line, values_map=False):
        values_map = values_map if values_map else self.default_tax_map
        return self.map_dict(tax_line, values_map)

    def get_cfdi_values_dict(self):
        return

    def dict_unsensitive_search(self, dict_search, keys_compare):

        """
        Search in a dictionary with different keys 'unsensitive', this is for the CFDI's with keys that ar the same for all of them 
        but one key is Upper or lower and doesnt match
        
        Arguments:
            dict_search {dict} -- Dictionary to search
            keys_compare {list} -- LIst of keys to iterate over the dict
        
        Returns:
            object -- If the keys are valid returns the object in dict. if the key not in dict return a empty str
        """
        if len(keys_compare) == 0:
            return dict_search
        if not isinstance(dict_search, dict):
            return ''
        key_compare = keys_compare.pop(0)
        for key, value in dict_search.items():
            if key.lower() == key_compare.lower():
                return self.dict_unsensitive_search(value, keys_compare)
        return ''

    def check_xml_structure(self):
        """
        Check XML structure with XSD file.
        Arguments:
            data {bytes} -- b64 encoded.
        Returns:
            [True] -- If is a valid return True, return the error string if any error ocurred.
        """

        attachment = self.odoo_obj.env['ir.attachment'].search([('name', '=', 'l10n_mx_edi.cfdv40.xsd')], False)
        # attachment = self.odoo_obj.env['ir.attachment'].search([('name', '=', 'l10n_mx_edi.cfdv33.xsd')], False)
        tree = base64.b64decode(self.b64_file)
        xsd_datas = base64.b64decode(attachment.sudo().datas) if attachment else False
        if xsd_datas:
            try:
                tree = self.remove_extra_nodes(tree)
                with BytesIO(xsd_datas) as xsd:
                    _check_with_xsd(tree, xsd)
                    return True
            except Exception as e:
                raise ValidationError(_("Error validating the file %s") % e)
        else:
            raise ValidationError(_("Could not retrieve xsd file for validation"))

    def remove_extra_nodes(self, xml):
        tree = self.get_tree(xml)
        namspaces = {'cfdi': 'http://www.sat.gob.mx/cfd/3'}
        tree = self.remove_addendas(tree, namspaces)
        return etree.tostring(tree, encoding='utf8', method='xml')

    def get_tree(self, xml):
        parser = etree.XMLParser(encoding='utf-8', recover=True)
        tree = etree.parse(BytesIO(xml), parser)
        return tree

    def remove_addendas(self, tree, namspaces):
        for addenda in tree.xpath("//cfdi:Addenda", namespaces=namspaces):
            addenda.getparent().remove(addenda)
        return tree

    def get_sat_status(self):
        '''
        Check the xml data in SAT WS to get status.
        '''
        url = 'https://consultaqr.facturaelectronica.sat.gob.mx/ConsultaCFDIService.svc?wsdl'
        headers = {'SOAPAction': 'http://tempuri.org/IConsultaCFDIService/Consulta', 'Content-Type': 'text/xml; charset=utf-8'}
        template = """<?xml version="1.0" encoding="UTF-8"?>
                    <SOAP-ENV:Envelope xmlns:ns0="http://tempuri.org/" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                    xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
                    <SOAP-ENV:Header/>
                    <ns1:Body>
                        <ns0:Consulta>
                            <ns0:expresionImpresa>${data}</ns0:expresionImpresa>
                        </ns0:Consulta>
                    </ns1:Body>
                    </SOAP-ENV:Envelope>"""
        namespace = {'a': 'http://schemas.datacontract.org/2004/07/Sat.Cfdi.Negocio.ConsultaCfdi.Servicio'}

        supplier_rfc = self.get_supplier_vat()
        customer_rfc = self.get_customer_vat()
        total = self.get_amount_total()
        uuid = self.get_uuid()
        params = '?re=%s&amp;rr=%s&amp;tt=%s&amp;id=%s' % (
            tools.html_escape(tools.html_escape(supplier_rfc or '')),
            tools.html_escape(tools.html_escape(customer_rfc or '')),
            total or 0.0, uuid or '')
        soap_env = template.format(data=params)
        try:
            soap_xml = requests.post(url, data=soap_env,
                                     headers=headers, timeout=20)
            response = fromstring(soap_xml.text)
            status = response.xpath(
                '//a:Estado', namespaces=namespace)
        except Exception as e:
            return {'error': e}
        return CFDI_SAT_QR_STATE.get(status[0] if status else '', 'none')
