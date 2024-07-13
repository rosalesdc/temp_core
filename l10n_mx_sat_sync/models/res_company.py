#########################################################
# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2023 Birtum - https://www.birtum.com
# All Rights Reserved.
#
# Developer(s): Eddy Luis Pérez Vila <epv@birtum.com>
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
##########################################################
import base64
import logging
import time

from dateutil.relativedelta import relativedelta
from lxml import etree
from lxml.objectify import fromstring
from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .portal_sat import PortalSAT

_logger = logging.getLogger(__name__)

TRY_COUNT = 3


class ResCompany(models.Model):
    _inherit = "res.company"

    last_cfdi_fetch_date = fields.Datetime(
        "Last CFDI fetch date", readonly=False)
    l10n_mx_edi_esign_ids = fields.Many2many(
        "l10n_mx_edi.certificate",
        relation="l10n_mx_edi_esign_ids",
        string="FIEL certificate",
        domain="[('is_esign','=',True)]",
    )

    type_operation_sat = fields.Many2many(
        comodel_name="type.operation.sat",
        relation="company_type_operation_sat_rel",
        column1="company_id",
        column2="operation_sat_id",
        string="Type SAT Operation",
    )
    load_data_master_from_xml = fields.Boolean(
        'Load master data from XML'
    )

    @api.model
    def auto_import_cfdi_invoices(self):
        for company in self.search([("l10n_mx_edi_esign_ids", "!=", False)]):
            company.download_cfdi_invoices()
        return True

    @api.model
    def import_current_company_invoice(self):
        self.env.company.with_user(self.env.user).download_cfdi_invoices()
        return True

    def _l10n_mx_edi_decode_cfdi(self, uuid, cfdi_data=None):
        """Helper to extract relevant data from the CFDI to be used, for example, when printing the invoice.
        :param cfdi_data:   The optional cfdi data.
        :return:            A python dictionary.
        """

        def get_tfd_node(cfdi_node, attribute, namespaces):
            if hasattr(cfdi_node, "Complemento"):
                node = cfdi_node.Complemento.xpath(
                    attribute, namespaces=namespaces)
                return node[0] if node else None
            else:
                return None

        def get_partners_info(emisor_node, receptor_node):
            data = {
                "issuing_partner_vat": emisor_node.get("Rfc", emisor_node.get("rfc")),
                "issuing_partner": emisor_node.get("Nombre", emisor_node.get("nombre"))
                or _("Not define"),
                "receiver_partner_vat": receptor_node.get(
                    "Rfc", receptor_node.get("rfc")
                ),
                "receiver_partner": receptor_node.get(
                    "Nombre", receptor_node.get("nombre")
                )
                or _("Not define"),
            }
            company = self.env.company
            data["issuing_type"] = (
                "I" if company.vat == data["issuing_partner_vat"] else "R"
            )
            return data

        def get_payment_node(cfdi_node, attribute, namespaces):
            if hasattr(cfdi_node, "Complemento"):
                node = cfdi_node.Complemento.xpath(
                    attribute, namespaces=namespaces)
                return node[0] if node else None
            else:
                return None

        # Nothing to decode.
        if not cfdi_data:
            return {}

        try:
            cfdi_node = fromstring(cfdi_data)
            emisor_node = cfdi_node.Emisor
            receptor_node = cfdi_node.Receptor
        except etree.XMLSyntaxError as e:
            _logger.error("Cannot open CFDI data (%s) beacuse: %s" % (uuid, e))
            return {}
        except AttributeError as e:
            _logger.error("Cannot open CFDI data (%s) beacuse: %s" % (uuid, e))
            return {}

        tfd_node = get_tfd_node(
            cfdi_node,
            "tfd:TimbreFiscalDigital[1]",
            {"tfd": "http://www.sat.gob.mx/TimbreFiscalDigital"},
        )

        partners_info = get_partners_info(emisor_node, receptor_node)

        cfdi_data = {
            "issuing_partner_vat": partners_info["issuing_partner_vat"],
            "issuing_partner": partners_info["issuing_partner"],
            "receiver_partner_vat": partners_info["receiver_partner_vat"],
            "receiver_partner": partners_info["receiver_partner"],
            "issuing_type": partners_info["issuing_type"],
            "number": cfdi_node.get("Folio", cfdi_node.get("folio")),
            "series": cfdi_node.get("Serie", cfdi_node.get("serie")),
            "type": cfdi_node.get("TipoDeComprobante"),
            "version": cfdi_node.get("Version", cfdi_node.get("version")),
            "currency": cfdi_node.get("Moneda", cfdi_node.get("moneda")),
            "rate": cfdi_node.get("TipoCambio", 1),
            "amount_total": cfdi_node.get("Total", cfdi_node.get("total")),
            "payment_method": cfdi_node.get("MetodoPago", cfdi_node.get("metodoPago")),
            "payment_way": cfdi_node.get("FormaPago", cfdi_node.get("formaPago")),
            "emission_date_str": cfdi_node.get(
                "fecha", cfdi_node.get("Fecha", "")
            ).replace("T", " "),
            "stamp_date": tfd_node is not None
            and tfd_node.get("FechaTimbrado", "").replace("T", " "),
        }
        payment_node = None
        if cfdi_node.get("TipoDeComprobante") == "P":
            payment_node = get_payment_node(
                cfdi_node,
                "pago20:Pagos"
                if cfdi_node.get("Version", cfdi_node.get("version")) == "4.0"
                else "pago10:Pagos",
                {
                    "pago10": "http://www.sat.gob.mx/Pagos",
                    "pago20": "http://www.sat.gob.mx/Pagos20",
                },
            )
            try:
                payment_child = payment_node.Pago
                cfdi_data.update(
                    {
                        "currency": payment_child.get(
                            "MonedaP", payment_child.get("monedaP")
                        ),
                        "rate": cfdi_node.get("TipoCambioP", 1),
                        "amount_total": payment_child.get(
                            "Monto", payment_child.get("monto")
                        ),
                        "payment_way": payment_child.get(
                            "FormaDePagoP", payment_child.get("formaDePagoP")
                        ),
                    }
                )
            except Exception as e:
                _logger.error("Cannot open CFDI payment node: %s" % e)
        return cfdi_data

    def download_cfdi_invoices_cron(self):
        self.env.company.download_cfdi_invoices()

    def download_cfdi_invoices(self, start_date=False, end_date=False):
        if not self.type_operation_sat:
            self.download_cfdi_invoices_aux(start_date, end_date)
        else:
            for r in self.type_operation_sat:
                self.download_cfdi_invoices_aux(
                    start_date, end_date, type_op=str(r.code)
                )
        # Validación para obtener una FIEL válida

    def download_cfdi_invoices_aux(
        self, start_date=False, end_date=False, type_op="-1", uuid=False
    ):
        if not end_date:
            end_date = fields.Datetime.context_timestamp(
                self, fields.Datetime.now())

        if not start_date:
            if self.last_cfdi_fetch_date:
                start_date = fields.Datetime.context_timestamp(
                    self, self.last_cfdi_fetch_date
                )
            else:
                now_date = fields.Datetime.now().replace(hour=0, minute=0)
                start_date = fields.Datetime.context_timestamp(self, now_date)

        esignature = self.l10n_mx_edi_esign_ids.with_user(
            self.env.user
        )._get_valid_certificate()
        if not esignature:
            raise UserError(_("Files uploaded are not FIEL files."))
        if not esignature.content or not esignature.key or not esignature.password:
            raise UserError(_("Select the correct FIEL files (.cer or .pem)."))
        # Diccionario para request al SAT
        opt = {
            "credenciales": None,
            "rfc": None,
            "uuid": uuid if uuid else None,
            "ano": None,
            "mes": None,
            "dia": 0,
            "intervalo_dias": None,
            "fecha_inicial": None,
            "fecha_final": None,
            "tipo": "t",
            "tipo_complemento": type_op,
            "rfc_emisor": None,
            "rfc_receptor": None,
            "sin_descargar": False,
            "base_datos": False,
            "directorio_fiel": "",
            "archivo_uuids": "",
            "estatus": False,
        }
        if start_date and end_date:
            opt["fecha_inicial"] = start_date
            opt["fecha_final"] = end_date

        # Conexión al SAT y request para obtener documentos
        fiel_cert_data = base64.b64decode(esignature.content)
        fiel_pem_data = esignature._get_pem_key(
            esignature.key, esignature.password)
        sat = None
        for i in range(TRY_COUNT):
            sat = PortalSAT(opt["rfc"], "cfdi-descarga", False)
            if sat.login_fiel(fiel_cert_data, fiel_pem_data):
                time.sleep(1)
                break
        supplier_invoices_data, issued_invoices_data = {}, {}
        if sat and sat.is_connect:
            supplier_invoices_data, issued_invoices_data = sat.search(opt)
            sat.logout()
        elif sat:
            sat.logout()

        # Procesamiento de documentos obtenidos del SAT
        if not supplier_invoices_data and not issued_invoices_data:
            return

        Document = self.env["sat.documents"]
        filter_start_date = opt["fecha_inicial"] - relativedelta(days=1)
        filter_end_date = opt["fecha_final"] + relativedelta(days=1)
        uuid_list = list(supplier_invoices_data.keys()) + list(
            issued_invoices_data.keys()
        )
        sat_docs = (supplier_invoices_data, issued_invoices_data)
        documents = (
            Document.sudo()
            .search(
                [
                    ("name", "in", uuid_list),
                    ("date", ">=", filter_start_date),
                    ("date", "<=", filter_end_date),
                ]
            )
            .mapped("name")
        )
        notes = None
        vals = []

        def get_currency_id(currency_str, notes):
            if not currency_str:
                _(
                    "This currency has not could not be read from CFDI. Contact support to fixed."
                )
                return self.env.ref("base.MXN", raise_if_not_found=False).id
            currency = self.env.ref(
                "base." + str(currency_str), raise_if_not_found=False)
            if currency:
                return (
                    currency.id,
                )
            else:
                return False

        for sat_doc in sat_docs:
            _logger.info("Processing %s CFDI documents." %
                         len(sat_doc.items()))
            for uuid, data in sat_doc.items():
                uuid = uuid.upper()
                if uuid in documents:
                    continue
                xml_content = data[1]
                # Validación extra para evitar errores de NS
                if b"xmlns:schemaLocation" in xml_content:
                    xml_content = xml_content.replace(
                        b"xmlns:schemaLocation", b"xsi:schemaLocation"
                    )
                cfdi_data = self._l10n_mx_edi_decode_cfdi(uuid, xml_content)
                if not cfdi_data:
                    continue
                if not get_currency_id(
                    cfdi_data.get("currency"), notes
                ):
                    continue
                vals.append(
                    {
                        "name": uuid,
                        "number": cfdi_data.get("number", ""),
                        "series": cfdi_data.get("series", ""),
                        "date": cfdi_data.get("emission_date_str"),
                        "stamp_date": cfdi_data.get("stamp_date"),
                        "payment_method": cfdi_data.get("payment_method"),
                        "payment_way_id": self.env["l10n_mx_edi.payment.method"]
                        .search(
                            [("code", "=", cfdi_data.get("payment_way", "00"))], limit=1
                        )
                        .id,
                        "currency_id": get_currency_id(
                            cfdi_data.get("currency"), notes
                        ),
                        "currency_rate": float(cfdi_data.get("rate", 1)),
                        "amount": float(cfdi_data.get("amount_total"))
                        if cfdi_data.get("amount_total")
                        else 0,
                        "issuing_partner": cfdi_data.get("issuing_partner"),
                        "issuing_partner_vat": cfdi_data.get("issuing_partner_vat"),
                        "receiver_partner": cfdi_data.get("receiver_partner"),
                        "receiver_partner_vat": cfdi_data.get("receiver_partner_vat"),
                        "cfdi_type": cfdi_data.get("type"),
                        "issuing_type": cfdi_data.get("issuing_type"),
                        "cfdi_version": cfdi_data.get("version"),
                        "notes": notes,
                        "xml_attachment": base64.b64encode(xml_content),
                        "xml_filename": uuid + ".xml",
                        "company_id": self.env.company.id,
                    }
                )

        try:
            Document.create(vals)
        except Exception as e:
            _logger.error("Cannot create SAT Document for the error: %s" % e)

        self.last_cfdi_fetch_date = fields.Datetime.now()
        return
