#!/usr/bin/python
# -*- coding: utf-8 -*-
###############################################################################
#
# ODOO (ex OpenERP)
# Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<https://micronaet.com>)
# Developer: Nicola Riolini @thebrush (<https://it.linkedin.com/in/thebrush>)
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

# Standard:
import os
import sys

# Access:
import erppeek
import ConfigParser

# Utilty:
from utility import *
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# Read configuration parameter:
# -----------------------------------------------------------------------------
cfg_file = os.path.expanduser('./portal.cfg')
config = ConfigParser.ConfigParser()
config.read([cfg_file])

# -----------------------------------------------------------------------------
# Parameters:
# -----------------------------------------------------------------------------
# ODOO:
hostname = config.get('portal', 'hostname')
username = config.get('portal', 'username')
password = config.get('portal', 'password')
database = config.get('portal', 'database')
port = eval(config.get('portal', 'port'))

# Folder:
folder = os.path.expanduser(config.get('folder', 'input'))

deadline_fullname = os.path.expanduser(config.get('fullname', 'deadline'))
order_fullname = os.path.expanduser(config.get('fullname', 'order'))

# Log files:
schedule_log = os.path.expanduser(config.get('log', 'schedule'))
f_schedule = open(schedule_log, 'a')

activity_log = os.path.expanduser(config.get('log', 'activity'))
f_activity = open(activity_log, 'a')

# -----------------------------------------------------------------------------
# Connect to ODOO:
# -----------------------------------------------------------------------------
odoo = erppeek.Client(
    'http://%s:%s' % (hostname, port),
    db=database, user=username, password=password,
    )

# -----------------------------------------------------------------------------
#                                      START:
# -----------------------------------------------------------------------------
log_data('Start import procedure', f_schedule)
log_data('ODOO Connection: %s' % odoo, f_activity)

# -----------------------------------------------------------------------------
#                                     PARTNER:
# -----------------------------------------------------------------------------
partner_pool = odoo.model('res.partner')
user_pool = odoo.model('res.users')

file_csv = os.path.join(folder, 'partner.csv')
log_data('Start import partner from %s' % file_csv, f_activity)

# Create partner:
update_user_ids = partner_pool.import_csv_partner_data(
    file_csv, user_creation=False)

# Create user procedure:
# Note: moved here instead of ODOO module procedure (for rollback error)
update_list = [] # (partner_id, user_id)
total_user = len(update_user_ids)
log_data('User list # %s' % total_user, f_activity)

i = 0
new_users = ''
for partner in partner_pool.browse(update_user_ids):
    i += 1
    if i % 10 == 0:
        print 'User create/update: %s / %s' % (i, total_user)
    ref = partner.ref
    if not ref:
        continue
    if partner.portal_user_id:
        continue # yet present

    user_ids = user_pool.search([
        ('login', '=', partner.ref),
        ])
    if user_ids:
        # TODO manage multiple
        user_id = user_ids[0]
    else:
        first_password = get_random_password(10)
        new_users += '[%s] ' % ref
        user_id = user_pool.create({
            'active': True,
            'login': ref,
            'first_password': first_password,
            'password': first_password,
            'partner_id': partner.id,
            #'name': 'User: %s' % partner.name,
            'signature': partner.name,
            })
    update_list.append((partner.id, user_id.id))

log_data('New users: %s' % new_users, f_activity)

# Update portal user for partner:
for partner_id, user_id in update_list:
    partner_pool.write(partner_id, {
        'portal_user_id': user_id,
        })

# Link user to partner updated
#partner_pool.create_portal_user(update_user_ids)
log_data('End import partner from %s' % file_csv, f_activity)

# -----------------------------------------------------------------------------
#                                     DEADLINE:
# -----------------------------------------------------------------------------
deadline_pool = odoo.model('portal.deadline')
log_data('Start import deadline from %s' % deadline_fullname, f_activity)
deadline_pool.schedule_etl_accounting_deadline(deadline_fullname)
log_data('End import o from %s' % deadline_fullname, f_activity)

# -----------------------------------------------------------------------------
#                                     ORDER:
# -----------------------------------------------------------------------------
order_pool = odoo.model('portal.sale.order')
log_data('Start import order from %s' % order_fullname, f_activity)
order_pool.schedule_etl_accounting_order(order_fullname)
log_data('End import order from %s' % order_fullname, f_activity)

# -----------------------------------------------------------------------------
#                                  END OPERATION:
# -----------------------------------------------------------------------------
log_data('End import procedure', f_schedule)

# Close log files:
f_schedule.close()
f_activity.close()
