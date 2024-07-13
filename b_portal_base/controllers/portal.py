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

from odoo import http, _
from odoo.exceptions import ValidationError, RedirectWarning
from odoo.http import request, content_disposition
from odoo.exceptions import ValidationError, RedirectWarning
from odoo.tools.translate import _
from odoo.addons.portal.controllers.portal import pager
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from io import StringIO
import base64
from io import BytesIO, StringIO
import csv

mes_err = lambda e: e.name if vars(e).get("name", False) else str(e)


class PortalProvider(CustomerPortal):
    _items_per_page = 20

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'products_count' in counters:
            products = self.get_products()
            products_count = len(products) if len(products) > 0 else 0
            values['products_count'] = products_count
        return values

    @http.route(['/my/products', '/my/products/page/<int:page>'], type='http', auth='user', website=True)
    def my_products(self, page=1, **kw):
        """
        Controller por my products page.
        Args:
            page (int, optional): Page. Defaults to 1.
        Returns:
            template: Template.
        """
        values = {}
        user = request.env.user
        products = self.get_products()
        # count for pager
        product_count = len(products)
        # make pager
        _pager = pager(
            url="/my/products",
            total=product_count,
            page=page,
            step=self._items_per_page
        )
        # search the products to display, according to the pager data
        if len(products) > self._items_per_page:
            init = _pager['offset']
            end = -1 if (_pager['offset'] + product_count) > len(products) else _pager['offset'] + product_count
            products = products[init: end]

        values.update({
            'products': products,
            'partner_id': user.partner_id.id,
            'page_name': 'products',
            'pager': _pager,
            'sortby': None,
            'filterby': None,
            'default_url': '/my/products',
        })
        return request.render('b_portal_base.portal_base_my_products', values)

    def get_products(self):
        user = request.env.user
        supplier_ids = request.env['product.provider.info'].sudo().search([('partner_id', '=', user.partner_id.id)])
        supplier_ids = [supp.id for supp in supplier_ids]
        return request.env['product.product'].sudo().search([('provider_ids', 'in', supplier_ids)])

    @http.route('/update_sku', auth='user', type='json', website=True, csrf=False)
    def update_sku(self, vals, **post):
        """
        Controller for update sku.
        Args:
            vals (dict): values to update.
        Returns:
            dict: Response
        """
        if vals.get('sku', '') == '':
            return {'header': 'Error', 'message': _('The SKU field is empty.'), 'status': 0}

        p = request.env['product.product'].sudo().browse(int(vals.get('product_id')))
        user = request.env.user
        seller_id = p.provider_ids.filtered(lambda s: s.partner_id.id == user.partner_id.id)

        if seller_id.product_sku == vals.get('sku', ''):
            return {'header': _('Warning'), 'message': _('The SKU is the same as the system. It was not updated.'), 'status': 1}

        response = seller_id.sudo().write({'product_sku': vals.get('sku')})
        if response:
            return {'header': _('Sucess'), 'message': _('The SKU has been successfully updated'), 'status': 2}

        return {'header': _('Error'), 'message': _('An error has been ocurred'), 'status': 0}

    @http.route('/export_product_csv', auth='user', type='http', website=True, csrf=False)
    def export_csv(self):
        """
        Controller for export csv.
        Returns:
            dict: response.
        """
        user = request.env.user
        products = self.get_products()
        filename = 'product_list_{}.csv'.format(user.name)
        file = StringIO()
        # CSV writer
        product_file_writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        product_file_writer.writerow(['id', 'name', 'product_uom', 'product_sku'])
        for product in products:
            provider = product.provider_ids.filtered(lambda p: p.partner_id.id == user.partner_id.id)
            product_file_writer.writerow([product.id, product.name, product.uom_name, provider.product_sku])
        header = [
            ('Content-Type', 'text/csv'),
            ("Content-Disposition", content_disposition(filename)),
        ]
        return request.make_response(file.getvalue(), headers=header)

    @http.route('/import_product_csv', auth='user', type='json', website=True, csrf=False)
    def import_csv(self, vals, **post):
        """
        Controller for import csv.
        Args:
            vals (dict): csv with sku's.
        Returns:
            dict: response.
        """
        data = vals.get('data', False)
        filename = vals.get('fname', "")
        b64_data = data.split(',')[1]
        if not filename.lower().endswith(".csv"):
            raise ValidationError(_('File type not accepted'))

        if not b64_data:
            raise ValidationError(_('File no content'))

        file = StringIO(base64.b64decode(b64_data).decode("utf-8"))
        csv_reader = csv.reader(file, delimiter=",")
        rows = list(csv_reader)
        header = rows[0]
        _id = header.index("id")
        _sku = header.index("product_sku")
        for row in rows[1:]:
            id, sku = int(row[_id]), row[_sku]
            product = request.env["product.product"].sudo().browse(id)
            self.update_product_sku(product, sku)
        return {'header': _('Success'), 'message': _('The SKUs has been updated'), 'status': 2}

    def update_product_sku(self, product, new_sku):
        partner_id = request.env.user.partner_id.id
        provider_id = product.provider_ids.filtered(lambda p: p.partner_id.id == partner_id)
        if provider_id.product_sku == new_sku:
            return True
        return provider_id.write({'product_sku': new_sku})
