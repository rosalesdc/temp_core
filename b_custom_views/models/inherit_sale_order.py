# -*- encoding: utf-8 -*-
#
# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2023 Birtum - http://www.birtum.com/
# All Rights Reserved.
#
# Developer(s): Eddy Luis Pérez Vila
#               (epv@birtum.com)
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
from odoo import models, fields, api

from datetime import datetime, timedelta


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    show_margin = fields.Boolean(
        'Show Margin',
        compute='_show_sale_margin',
    )
    # margin = fields.Monetary("Margin", compute='_compute_margin',
    #                          store=True, groups="b_custom_views.group_user_show_sale_margin")

    def _show_sale_margin(self):
        for record in self:
            if self.env.user.has_group('b_custom_views.group_user_show_sale_margin'):
                record.show_margin = True
            else:
                record.show_margin = False

from odoo import fields, models


class SaleReport(models.Model):
    _inherit = 'sale.report'

    margin = fields.Float('Margin', groups="b_custom_views.group_user_show_sale_margin")

    # def _select_additional_fields(self):
    #     res = super()._select_additional_fields()
    #     if self.env.user.has_group('b_custom_views.group_user_show_sale_margin'):
    #         res['margin'] = f"""SUM(l.margin
    #             / {self._case_value_or_one('s.currency_rate')}
    #             * {self._case_value_or_one('currency_table.rate')})
    #         """
    #     else:
    #         res['margin'] = 0
    #     return res