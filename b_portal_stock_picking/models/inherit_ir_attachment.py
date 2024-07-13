# -*- encoding: utf-8 -*-
#
# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2023 Birtum - https://www.birtum.com
# All Rights Reserved.
#
# Developer(s): Alan Guzmán
#               age@wedoo.tech
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
from odoo import models, fields, api


class IrAttchment(models.Model):
    _inherit = 'ir.attachment'

    portal_provider = fields.Boolean(
        default=False,
        help='Este campo será True cuando el XML haya sido importado desde el portal de proveedores'
    )

    def check_valid_uuid(self):
        for attach in self:
            if not attach.portal_provider:
                super(IrAttchment, attach).check_valid_uuid()
            invoice_id = self.env['account.move'].sudo().browse(attach.res_id)
            invoice_id.l10n_mx_edi_cfdi_uuid = False
            invoice_id.l10n_mx_edi_cfdi_name = False
