# -*- encoding: utf-8 -*-
#
# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2023 Birtum - https://www.birtum.com
# All Rights Reserved.
#
# Developer(s): David Rosales
#               drc@birtum.com
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

import logging
from odoo import models, fields, api, _
_logger = logging.getLogger(__name__)


class SoIntegratedData(models.Model):
    _name = 'so.integrated.data'
    _description = 'Sales Integrated Data'
    # Model that receives the data to create a sale order

    name = fields.Char(
        string='Sale Order ARX',
        copy=False,
        help='ID from ARX',
    )

    partner = fields.Json(
        string='Partner',
        copy=False,
        help='Data to create/update Sale Order Partner',
    )

    invoice_address = fields.Json(
        string='Invoice Address',
        help='Data to create/update invoice address',
    )

    shipping_address = fields.Json(
        string='Shipping Address',
        help='Data to create/update shipping address',
    )

    productos = fields.Json(
        string='Productos',
        help='Data to create/update products',
    )

    sale_order = fields.Json(
        string='Sale Order',
        help='Data to create sale order',
    )

    sale_order_line = fields.Json(
        string='Sale Order Line',
        help='Data to create sale order lines',
    )

    payment = fields.Json(
        string='Payment',
        help='Data to create related payment',
    )

    validation_msj = fields.Char(
        string="Validation message",
        help='Validation message',
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Attempt to create/update:
        -Partner
        -Sale order
        -Sale order lines
        -Related Payment
        """
        res = super(SoIntegratedData, self).create(vals_list)
        for record in res:
            logging.info(("Init sale process"))
            #partner_id, invoice_address_id, shipping_address_id = record.partner_process()
            logging.info(("Partner_data----------------%s"%(record.name)))
            logging.info(("Partner_data----------------%s"%(record.partner)))
            logging.info(("Products_data----------------%s"%(record.productos)))
            logging.info(("Order_data----------------%s"%(record.sale_order)))
            logging.info(("Lines_data----------------%s"%(record.sale_order_line)))
            logging.info(("Payment_data----------------%s"%(record.payment)))
            logging.info(("END PROCEESS--------------------"))
            #prods = record.product_process()
            #logging.info(("Products created"))
            #order_id = record.sale_order_process(
            #    partner_id, invoice_address_id, shipping_address_id)
            #logging.info(("Order created"))
            #record.order_line_process(order_id.id, prods)
            #logging.info(("Lines created"))
            #record.name = order_id.arx_name
            #order_id.action_confirm()
            #logging.info(("Order confirmed"))
            #if self.payment:
            #    record.payment_process(order_id)
            #    logging.info(("Payment created"))
        return res

    def partner_process(self):
        '''Validate partner data to create/update records
        '''
        parent = False
        if self.partner:
            partner_id = self.env['res.partner'].search(
                [('id_arx', '=', self.partner['id_arx'])])
            if partner_id:
                partner_id.write(self.partner)
                parent = partner_id
            else:
                parent = self.env['res.partner'].create(
                    self.partner
                )
        if self.invoice_address and parent:
            invoice_address_id = self.env['res.partner'].search(
                [('id_arx', '=', self.invoice_address['id_arx'])])
            dict_invoice_address = self.invoice_address
            # ADD key parent_id for invoice address
            dict_invoice_address["parent_id"] = parent.id
            if invoice_address_id:
                invoice_address_id.write(dict_invoice_address)
            else:
                invoice_address_id = self.env['res.partner'].create(
                    dict_invoice_address
                )
            invoice_address_id.parent_id = parent.id

        if self.shipping_address and parent:
            shipping_address_id = self.env['res.partner'].search(
                [('id_arx', '=', self.shipping_address['id_arx'])])
            dict_shipping = self.shipping_address
            # ADD key parent_id for shipping address
            dict_shipping["parent_id"] = parent.id
            if shipping_address_id:
                shipping_address_id.write(dict_shipping)
            else:
                shipping_address_id = self.env['res.partner'].create(
                    dict_shipping
                )
        logging.info(("end partner FUNCTION----------------"))
        return parent.id, invoice_address_id.id, shipping_address_id.id

    def product_process(self):
        '''Validate products data to create/update records
        -Returns a dictionary with code-identifiers so as not to be looked up later.
        '''
        logging.info(("INIT products FUNCTION----------------%s"%(self.productos)))
        dict_prod = {}
        for prod in self.productos:
            logging.warning(("Products -------------1"))
            product_id = self.env['product.product'].search(
                [('default_code', '=', prod['default_code'])])
            if product_id:
                logging.warning(("Products -------------2"))
                product_id.write(prod)
                logging.warning(("Products -------------3"))
            else:
                logging.warning(("Products -------------4"))
                product_id = self.env['product.product'].create(
                    prod
                )
                logging.warning(("Products -------------5"))
                # If new product, create a seller
                self.env['product.supplierinfo'].create(
                    {
                        'partner_id': self.env.company.main_supplier.id,
                        'price': prod['standard_price'],
                        'product_id': product_id.id
                    }
                )
                logging.warning(("Products -------------6"))
            dict_prod[product_id.default_code] = product_id.id
            logging.warning(("Products -------------7"))
        logging.warning(("Products -------------8"))
        return dict_prod

    def sale_order_process(self, partner, inv_address, shipping_address):
        '''Create order, set partner_invoice_id, partner_shipping_id 
        previously created values 
        '''
        order_dict = self.sale_order
        order_dict['partner_id'] = partner
        order_dict['partner_invoice_id'] = inv_address
        order_dict['partner_shipping_id'] = shipping_address
        new_order = self.env['sale.order'].create(
            order_dict
        )
        return new_order

    def order_line_process(self, order, products):
        '''Create Sale Order Lines
        '''
        for line in self.sale_order_line:
            # In the JSON the default_code arrives in the product_id attribute,
            # in the following line it exchanges that value for the product id in Odoo
            line["product_id"] = products[line["product_id"]]
            line["order_id"] = order
            self.env['sale.order.line'].create(line)

    def payment_process(self, order):
        '''Creates the payment associated with the sale order
        '''
        pay_dict = self.payment
        pay_dict['partner_id'] = order.partner_id.id
        pay_dict['sale_order_id'] = order.id
        new_payment = self.env['account.payment'].create(
            pay_dict
        )
        new_payment.action_post()
        order.payment_arx = new_payment.id

    def msj_validation(self, move):
        '''Validates the status of the received invoice(s)
        '''
        if not move:
            self.msj_process = _('Move not found ')
            return False
        elif move.state != 'posted':
            self.msj_process = _('Move not posted')
            return False
        elif move.payment_state != 'not_paid':
            self.msj_process = _('Move with paymets')
            return False
        else:
            return True
