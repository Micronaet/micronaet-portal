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
import shutil
import MySQLdb
import MySQLdb.cursors
import ConfigParser
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# -----------------------------------------------------------------------------
# Read configuration parameter:
# -----------------------------------------------------------------------------
cfg_file = os.path.expanduser('./odoo.cfg')
config = ConfigParser.ConfigParser()
config.read([cfg_file])

# -----------------------------------------------------------------------------
# Parameters:
# -----------------------------------------------------------------------------
# MySQL Access
mysql = {
    'hostname': config.get('mysql', 'hostname'),
    'username': config.get('mysql', 'username'),
    'password': config.get('mysql', 'password'),

    'database': config.get('mysql', 'database'),
    'port': eval(config.get('mysql', 'port')),

    'capital': eval(config.get('mysql', 'capital')),
    }

# Transafer data:
folder = os.path.expanduser(config.get('transfer', 'folder'))
compress = os.path.expanduser(config.get('transfer', 'compress'))
publish = config.get('transfer', 'publish')
days = 365 # create user only for active partner

# File to copy in destination folder:
copy_files = eval(config.get('copy', 'origin'))


file_log = 'activity.log'
f_log = open(file_log, 'a')

# -----------------------------------------------------------------------------
#                                UTILITY FUNCTION:
# -----------------------------------------------------------------------------   
def mssql_connect(mysql):
    ''' Connect to partner MySQL table
    '''
    try: # Every error return no cursor
        return MySQLdb.connect(
            host=mysql['hostname'],
            user = mysql['username'],
            passwd = mysql['password'],
            db = mysql['database'],
            cursorclass=MySQLdb.cursors.DictCursor,
            charset='utf8',
            )
    except:
        return False

def clean_ascii(value):
    ''' Clean not ascii char
    '''
    value = value or ''
    res = ''
    for c in value:
        if ord(c) < 127:
            res += c
        else:    
            res += '*'
    return res

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
log_data('Start publish procedure', f_log)
connection = mssql_connect(mysql)
cursor = connection.cursor()
log_data('Connect with MySQL database: %s' % connection, f_log)

# -----------------------------------------------------------------------------
#                                 DEADLINE PAYMENT:
# -----------------------------------------------------------------------------   
log_data('Copy as is files: %s' % (copy_files, ), f_log)
for origin in copy_files:
    shutil.copy(origin, folder)

# -----------------------------------------------------------------------------
#                                     PARTNER: 
# -----------------------------------------------------------------------------   
table_extra = 'pc_progressivi'
table_rubrica = 'pa_rubr_pdc_clfr'
table_condition = 'pc_condizioni_comm'

file_csv = os.path.join(folder, 'partner.csv')
if mysql['capital']:
    table_rubrica = table_rubrica.upper()
    table_extra = table_extra.upper()
    table_condition = table_condition.upper()

log_data('Extract partner: %s, last delivery %s, condition: %s)' % (
    table_rubrica, table_extra, table_condition), f_log)

# -----------------------------------------------------------------------------
# A. Load active partner (date of delivery)
from_date = (datetime.now() - relativedelta(days=days)).strftime('%Y-%m-%d')
query = '''
    SELECT CKY_CNT FROM %s WHERE 
        DTT_ULT_CONSG >= '%s' AND CKY_CNT >= '2' AND CKY_CNT < '3';
    ''' % (table_extra, from_date)
log_data('Run SQL %s' % query, f_log)

cursor.execute(query)
user_db = [record['CKY_CNT'] for record in cursor]

# -----------------------------------------------------------------------------
# B. Load bank
query = '''
    SELECT * FROM %s WHERE CKY_CNT >= '2' AND CKY_CNT < '3';
    ''' % table_condition
log_data('Run SQL %s' % query, f_log)

cursor.execute(query)
bank_db = {}
for record in cursor:
    bank_db[record['CKY_CNT']] = u'Bank: %s [ABI: %s] [CAB: %s]' % (
        record['CDS_BANCA'],
        record['NGL_ABI'],
        record['NGL_CAB'],
        )

# -----------------------------------------------------------------------------
# C. Load partner list
query = '''
    SELECT * FROM %s WHERE CKY_CNT >= '2' AND CKY_CNT < '3';
    ''' % table_rubrica
log_data('Run SQL %s' % query, f_log)
cursor.execute(query)

i = 0
f_csv = open(file_csv, 'w')
for record in cursor:
    try:
        i += 1
        ref = record['CKY_CNT']        
        
        line = u'%s|%s|%s|%s|%s\n' % (
            ref,             
            record['CDS_CNT'], # name
            record['CDS_INDIR'], # street
            'X' if ref in user_db else '',
            bank_db.get(ref, 'Not present'),
            )
        f_csv.write(clean_ascii(line))
    except: 
        print 'Jump line error'
        continue    
f_csv.close()

# -----------------------------------------------------------------------------
#                                     ORDERS: 
# -----------------------------------------------------------------------------   
table_order = 'oc_testate'
table_line = 'oc_righe'

f_csv = os.path.join(folder, 'order.csv')
if mysql['capital']:
    table_order = table_rubrica.upper()
    table_line = table_extra.upper()

log_data('Extract order: %s, detail: %s)' % (
    table_order, table_line), f_log)

# -----------------------------------------------------------------------------
def get_key(record):
    ''' Key value generation:
    '''
    return '%s/%s/%s' % (
        record['CSG_DOC'],
        record['NGB_SR_DOC'],
        record['NGL_DOC'],        
        )

# A. OC Header
query = 'SELECT * FROM %s WHERE CSG_DOC="OC";' % table_order
log_data('Run SQL %s' % query, f_log)

cursor.execute(query)
order_db = {}
for record in cursor:
    key = get_key(record)
    order_db[key] = '%s|%s|%s|%s|%s|%s' % (
        key, 
        record['DTT_DOC'],
        record['CKY_CNT_CLFR'],
        record['CKY_CNT_SPED_ALT'],
        #record['NKY_CNT_AGENTE'],
        #record['IST_PORTO'],
        record['NKY_CAUM'],
        record['NKY_PAG'],
        record['CDS_NOTE'],
        )

# -----------------------------------------------------------------------------
# B. OC Line
query = 'SELECT * FROM %s;' % table_line
log_data('Run SQL %s' % query, f_log)

cursor.execute(query)
for record in cursor:
    key = get_key(record)
    header = order_db.get(key, '')
    if not header:
        continue # no header order now

    line = '%s|%s|%s|%s|%s|%s' % (
        header,
        record['NPR_RIGA'],

        record['DTT_SCAD'],
        record['CKY_ART'],
        record['CDS_VARIAZ_ART'],
        record['NPZ_UNIT'],
        record['NDC_QTA'],
        record['CKY_ART'],
        record['NQT_RIGA_O_PLOR'],
        record['NCF_CONV'],
        )
    f_csv.write(clean_ascii(line))
f_csv.close()

# -----------------------------------------------------------------------------
#                                  END OPERATION:
# -----------------------------------------------------------------------------   
# Publish command:        
log_data('Publish operation: %s' % publish, f_log)
os.system(publish)

# Close open files:
f_log.close()  




# -----------------------------------------------------------------------------
#                                     TRANSFER: 
# -----------------------------------------------------------------------------   
sys.exit()
import hashlib
from Crypto.Cipher import AES

# Generate key from password:
password = 'Micronaet'
key = hashlib.sha256(password).digest()
print 'Key used:', key
print 'Lungh.: ', len(key)
#key = '0123456789abcdef'
IV = 16 * '\x00'           # Initialization vector: discussed later
mode = AES.MODE_CBC
encryptor = AES.new(key, mode, IV=IV)

text = 'j' * 64 + 'i' * 128
ciphertext = encryptor.encrypt(text)
print '\nText: ', text, '\nCipher:', ciphertext


decryptor = AES.new(key, mode, IV=IV)
plain = decryptor.decrypt(ciphertext)
print '\nCipher:', ciphertext, '\nPlain: ', plain,
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
