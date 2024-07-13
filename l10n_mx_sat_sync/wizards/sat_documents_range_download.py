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
from odoo import fields, models


class SatDocumentsRangeDownload(models.TransientModel):
    _name = "sat.documents.range.download"
    _description = "Sat Documents Range Download Wizard"

    start_date = fields.Datetime(string="Start date", required=True)
    end_date = fields.Datetime(string="End date", required=True)

    _sql_constraints = [
        (
            "check_dates",
            "CHECK(end_date > start_date)",
            "End date must be higher than start date.",
        )
    ]

    def sat_documents_range_download(self):
        date_from = fields.Datetime.context_timestamp(self, self.start_date)
        date_to = fields.Datetime.context_timestamp(self, self.end_date)
        self.env.company.download_cfdi_invoices(date_from, date_to)
