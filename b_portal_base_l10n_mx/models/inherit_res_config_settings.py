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

from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    portal_xml_state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('posted', 'Posted')
        ],
        string='Default Portal Account Move Status',
        default_model="purchase.order",
        default='draft'
    )
    # activate_optional_purchase_validations = fields.Boolean(
    #     string='Activate extra validation for xml invoice creation for purchase. Install a module to add sku for products',
    #     default=False
    # )
    # activate_optional_sale_validations = fields.Boolean(
    #     string='Activate extra validation for xml invoice validation.',
    #     default=False
    # )
    activate_optional_sale_validations_line_leght = fields.Boolean(
        string='Check if the invoice has the same length of lines as the CFDI.',
        default=False
    )
    activate_optional_sale_validations_line = fields.Boolean(
        string='Check if the invoice has the same lines as the CFDI.',
        default=False
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param

        portal_xml_state = get_param('portal_xml_state', default='draft')
        # purchase_val = get_param('activate_optional_purchase_validations')
        sale_val_len = get_param('activate_optional_sale_validations_line_leght')
        sale_val_line = get_param('activate_optional_sale_validations_line')

        if not portal_xml_state:
            portal_xml_state = 'draft'

        # the value of the parameter is a nonempty string
        res.update(
            portal_xml_state=portal_xml_state,
            activate_optional_sale_validations_line_leght=sale_val_len,
            activate_optional_sale_validations_line=sale_val_line,
        )

        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param

        # we store the repr of the values, since the value of the parameter is a required string
        set_param('portal_xml_state', self.portal_xml_state)

        set_param("activate_optional_sale_validations_line_leght", self.activate_optional_sale_validations_line_leght,)
        set_param("activate_optional_sale_validations_line", self.activate_optional_sale_validations_line,)
