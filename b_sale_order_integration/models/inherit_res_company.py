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


from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    main_supplier = fields.Many2one(
        'res.partner',
        string='main_supplier',
        help='Used to set the default supplier when creating a new product in AppSynchro',
    )
