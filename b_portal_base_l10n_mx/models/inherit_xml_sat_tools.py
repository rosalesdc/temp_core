# -*- encoding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo.tools.translate import _

from odoo.addons.b_portal_base_l10n_mx.models.XmlSatTools import XmlSatTools


class PortalProviderXmlSatTools(XmlSatTools):

    def check_valid_vat(self, purchase_order):
        """
        Check valid vat.
        Args:
            purchase_order (purchase.order): Purchase order.
        Raises:
            ValidationError: The VAT of the sender does not correspond to that of the order
            ValidationError: The VAT of the receiver does not correspond to that of the order.
        """
        rfc_sender = self.get_supplier_vat()
        rfc_receiver = self.get_customer_vat()
        if self.odoo_obj.env.user.company_type == 'person':
            vat_emisor = self.odoo_obj.env.user.company_id.vat
        else:
            vat_emisor = self.odoo_obj.env.user.vat
        companies = self.odoo_obj.env['res.company'].sudo().search([])
        vat_company = [company.vat for company in companies]
        # print("Receptor ", vat_company)
        if rfc_sender != purchase_order.partner_id.vat:
            dont_match = "{} != {}".format(rfc_sender, vat_emisor)
            raise ValidationError(_("The VAT of the sender does not correspond to that of the order. %s") % dont_match)
        if rfc_receiver not in vat_company:
            dont_match = "{} not in {}".format(rfc_receiver, vat_company)
            raise ValidationError(_("The VAT of the receiver does not correspond to that of the order. %s") % dont_match)

    def _check_qty(self, concept, order_line):
        """
        Check the xml quantity with the order line to verify possible inconsistencies.
        Arguments:
            concept {dict} -- Contains the xml concept 
            order_line {order_line} -- Purchase order line.
        Returns:
            True -- Returns True if all checks passed, raise a error if any error ocurred
        """

        qty_val = order_line.product_qty - order_line.qty_invoiced
        qty_fac = order_line.qty_received - order_line.qty_invoiced
        xml_quantity = self.get_concept_quantity(concept)
        if float(xml_quantity) > qty_val:
            # return {'header' : 'Error', 'message' : 'La cantidad en el xml excede la cantidad que se puede facturar'}
            raise ValidationError(_('The amount in the xml exceeds the amount that can be billed.'))
        if float(xml_quantity) > qty_fac:
            # return  {'header' : 'Error', 'message' : 'La cantidad en el xml excede la cantidad recibida'}
            raise ValidationError(_('The quantity in the xml exceeds the quantity received.'))
        return True

    def get_concept_quantity(self, concept):
        return self.dict_unsensitive_search(concept, ['@Cantidad'])

    def get_concept_importe(self, concept):
        return self.dict_unsensitive_search(concept, ['@Importe'])

    def check_purchase_invoice(self, purchase_order):
        """
        Check if the purchase order match with the xml.
        Check qty.
        Check the price.
        Args:
            purchase_order (purchase.order): Purchase order to check.
        Raises:
            ValidationError: If the produc in xml is not present in the purchase order.
        Returns:
            True: If all checks pass.
        """
        concepts = self.get_concepts()
        acc_move = self.odoo_obj.env['account.move']
        total_xml = 0
        for concept in concepts:
            d_concept = self.get_concept_dict(concept)
            product = acc_move.get_product_from_concept(d_concept, self.xml_type, self)
            line = self.filter_po_line(purchase_order.order_line, product)
            if not line:
                raise ValidationError(_("The product %s is not present in the purchase order.") % product.name)
            self._check_qty(concept, line)
            self.validate_price(d_concept, line)
            total_xml += float(self.get_concept_importe(concept))
        self.validate_amount(total_xml, purchase_order)
        return True

    def filter_po_line(self, lines, product):
        return lines.filtered(lambda l: l.product_id.id == product.id)

    def validate_amount(self, total_xml, purchase_order):
        if total_xml > purchase_order.amount_total:
            raise ValidationError(_("The total amount of the invoice exceeds that of the order."))

    def validate_price(self, concept, line):
        if line.price_unit != float(concept.get('price_unit', 0.0)):
            raise ValidationError(_("The price of the product does not correspond to the price of the system."))
