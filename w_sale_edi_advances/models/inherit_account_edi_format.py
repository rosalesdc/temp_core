# -*- encoding: utf-8 -*-
#
# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2022 Birtum - https://www.birtum.com
# All Rights Reserved.
#
# Developer(s): Eddy Luis Pérez Vila
#               epv@birtum.com
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
#########################################################
from odoo import models


class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    def _post_invoice_edi(self, invoices):
        """
            inherit this method to set the advances as used.
        """
        if self.code != 'cfdi_3_3':
            return super(AccountEdiFormat, self)._post_invoice_edi(invoices)
        else:
            res = super(AccountEdiFormat, self)._post_invoice_edi(invoices)
            for invoice in invoices:
                item = res.get(invoice, False)
                if item and not 'error' in item and invoice.relate_advances:
                    # mark each advance invoice as related
                    for inv_rel in invoice.advance_ids:
                        inv_rel.advance_id.advance_related = True
        return res
