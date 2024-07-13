# -*- encoding: utf-8 -*-
#
# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2024 Birtum - https://www.birtum.com
# All Rights Reserved.
#
# Developer(s): Alan Guzmán
#               age@birtum.com
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
from odoo import models, fields, _
from odoo.exceptions import UserError
from collections import defaultdict
import re


class TrialBalanceCustomHandler(models.AbstractModel):
    _inherit = 'account.trial.balance.report.handler'

    def _l10n_mx_get_sat_values(self, options):
        report = self.env['account.report'].browse(options['report_id'])
        sat_options = self._l10n_mx_get_sat_options(options)
        report_lines = report._get_lines(sat_options)

        # The SAT code has to be of the form XXX.YY . Any additional suffixes are allowed, but if the line starts
        # with anything else it should not be included in the SAT report.
        sat_code = re.compile(r'((\d{3})\.\d{2})')

        account_lines = []
        parents = defaultdict(lambda: defaultdict(int))
        for line in [line for line in report_lines if line.get('level') == 4]:
            dummy, res_id = report._get_model_info_from_id(line['id'])
            account = self.env['account.account'].browse(res_id)
            is_credit_account = any([account.account_type.startswith(acc_type) for acc_type in ['liability', 'equity', 'income']])
            balance_sign = -1 if is_credit_account else 1
            cols = line.get('columns', [])
            # Initial Debit - Initial Credit = Initial Balance
            initial = balance_sign * (cols[0].get('no_format', 0.0) - cols[1].get('no_format', 0.0))
            # Debit and Credit of the selected period
            debit = cols[2].get('no_format', 0.0)
            credit = cols[3].get('no_format', 0.0)
            # End Debit - End Credit = End Balance
            end = balance_sign * (cols[4].get('no_format', 0.0) - cols[5].get('no_format', 0.0))
            pid_match = sat_code.match(line['name'])
            group_id = account.group_id
            # get the start prefix of the account group related to the current account
            group_code_start = group_id.code_prefix_start.split('.')[0]
            # get the start prefix of the current account
            account_start_code = line['name'].split('.')[0]
            if not pid_match:
                raise UserError(_("Invalid SAT code: %s", line['name']))
            for pid in pid_match.groups():
                # NOTE we have compare if the start prefix code of the group
                # related to the current account is not present in the start prefix code
                # of the account e.g.
                # parent account: 105.01
                # child account:  105.01.01
                # child account:  200.01.01
                # This two child account below by the group 105.01 Clientes nacionales but
                # the second account has a prefix of 200, this is different, the validation
                # is True and we have to sum the amounts to the parent account: 105.01 and
                # break the loop, otherwise, execute native code.
                if group_code_start not in account_start_code:
                    parents[group_code_start]['initial'] += initial
                    parents[group_code_start]['debit'] += debit
                    parents[group_code_start]['credit'] += credit
                    parents[group_code_start]['end'] += end
                    break
                else:
                    parents[pid]['initial'] += initial
                    parents[pid]['debit'] += debit
                    parents[pid]['credit'] += credit
                    parents[pid]['end'] += end
        for pid in sorted(parents.keys()):
            account_lines.append({
                'number': pid,
                'initial': '%.2f' % parents[pid]['initial'],
                'debit': '%.2f' % parents[pid]['debit'],
                'credit': '%.2f' % parents[pid]['credit'],
                'end': '%.2f' % parents[pid]['end'],
            })

        report_date = fields.Date.to_date(sat_options['date']['date_from'])
        return {
            'vat': self.env.company.vat or '',
            'month': str(report_date.month).zfill(2),
            'year': report_date.year,
            'type': 'N',
            'accounts': account_lines,
        }
