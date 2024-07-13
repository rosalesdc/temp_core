# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2020 Wedoo - http://www.wedoo.tech/
# All Rights Reserved.
#
# Developer(s): Randy La Rosa Alvarez
#               (rra@wedoo.tech)
#git stat
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

{
    'name': 'WEDOO | Synchronizer Odoo-Other System',
    'author': 'WEDOO ©',
    'category': 'Extra Tools',
    'sequence': 50,
    'summary': "Synchronize all tables between Odoo and other system.",
    'website': 'https://www.wedoo.tech',
    'version': '16.0.1.0.1',
    'depends': [
        'base',
        'base_setup'
    ],
    'installable': True,
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'data/groups_data.xml',
        'views/synchro_view.xml',
        'views/web_services_url.xml',
        'views/syncro_model.xml',
        'views/models_synchro.xml',
        'views/model_records_unlinked.xml',
        'views/inherit_res_config_settings.xml',
        'views/function_trigger.xml',

    ],
    'demo': [],
    'qweb': [],
    'application': False,
    'license': 'LGPL-3',

}
