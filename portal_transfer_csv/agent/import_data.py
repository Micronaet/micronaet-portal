# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2001-2014 Micronaet SRL (<http://www.micronaet.it>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import os
import sys
import MySQLdb
import MySQLdb.cursors
import ConfigParser
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

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
file_log = 'activity.log'

# -----------------------------------------------------------------------------
# Connect to ODOO:
# -----------------------------------------------------------------------------
odoo = erppeek.Client(
    'http://%s:%s' % (hostname, port), 
    db=database, user=username, password=password,
    )

# Transafer data:
f_log = open(file_log, 'a')

# -----------------------------------------------------------------------------
#                                UTILITY FUNCTION:
# -----------------------------------------------------------------------------   
def log_data(message, f_log, mode='INFO', verbose=True, cr='\n'):
    ''' Log data:
    '''
    message = '%s. [%s] %s%s' % (
        datetime.now(),
        mode,
        message,
        cr,
        )
    if verbose:
        print message.strip()
    f_log.write(message)
    return True

# -----------------------------------------------------------------------------
#                                      START: 
# -----------------------------------------------------------------------------   
log_data('Start import procedure', f_log)

# -----------------------------------------------------------------------------
#                                     PARTNER: 
# -----------------------------------------------------------------------------   
partner_pool = odoo.model('res.partner') 
file_csv = os.path.join(folder, 'partner.csv')
log_data('Start import partner from %s' % file_csv, f_log)
partner_pool.import_csv_partner_data(file_csv)#, user_creation=True)
log_data('End import partner from %s' % file_csv, f_log)




# -----------------------------------------------------------------------------
#                                  END OPERATION:
# -----------------------------------------------------------------------------   
f_log.close()