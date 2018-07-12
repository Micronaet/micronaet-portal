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

import os
import sys
import shutil
import MySQLdb
import MySQLdb.cursors
import ConfigParser
import hashlib
from Crypto.Cipher import AES
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
mysql1 = {
    'hostname': config.get('mysql1', 'hostname'),
    'username': config.get('mysql1', 'username'),
    'password': config.get('mysql1', 'password'),

    'database': config.get('mysql1', 'database'),
    'port': eval(config.get('mysql1', 'port')),

    'capital': eval(config.get('mysql1', 'capital')),
    }

mysql2 = {
    'hostname': config.get('mysql2', 'hostname'),
    'username': config.get('mysql2', 'username'),
    'password': config.get('mysql2', 'password'),

    'database': config.get('mysql2', 'database'),
    'port': eval(config.get('mysql2', 'port')),

    'capital': eval(config.get('mysql2', 'capital')),
    }

# Transafer data:
folder = os.path.expanduser(config.get('transfer', 'folder'))
compress = os.path.expanduser(config.get('transfer', 'compress'))
publish = config.get('transfer', 'publish')
password = config.get('transfer', 'password')
days = 365 # create user only for active partner

# File to copy in destination folder:
copy_files = eval(config.get('copy', 'origin'))

file_log = 'activity.log'
f_log = open(file_log, 'a')

# -----------------------------------------------------------------------------
#                                UTILITY FUNCTION:
# -----------------------------------------------------------------------------   
# SQL Connection function:
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

# Log function
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

# Format function:
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

def get_html_bank(record):
    ''' Rerturn HTML record for bank label for portal representation
    '''
    mask = '<p><b>Bank: </b>%s<br/><b>IBAN code: </b>%s<br/>'  + \
        '<b>BIC SWIFT code: </b>%s<br/></p>' 
    return mask % (
        record['CDS_BANCA'] or '/',
        record['CSG_IBAN_BBAN'] or '/',
        record['CSG_BIC'] or '/',
        )

def get_key(record):
    ''' Key value generation:
    '''
    return '%s/%s/%s' % (
        record['CSG_DOC'],
        record['NGB_SR_DOC'],
        record['NGL_DOC'],        
        )

# -----------------------------------------------------------------------------
#                                      START: 
# -----------------------------------------------------------------------------   
log_data('Start publish procedure', f_log)

connection1 = mssql_connect(mysql1)
cursor1 = connection1.cursor()
log_data('Connect with MySQL 1 database: %s' % connection1, f_log)

connection2 = mssql_connect(mysql2)
cursor2 = connection2.cursor()
log_data('Connect with MySQL 2 database: %s' % connection2, f_log)

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
table_payment = 'cp_pagamenti'
table_currency = 'mu_valute'
table_order = 'oc_testate'
table_line = 'oc_righe'
table_currency = 'mu_valute'

file_csv = os.path.join(folder, 'partner.csv')
if mysql1['capital']: # Use first SQL for check (are on the sasme server)
    table_rubrica = table_rubrica.upper()
    table_extra = table_extra.upper()
    table_condition = table_condition.upper()
    table_payment = table_payment.upper()
    table_currency = table_currency.upper()
    table_order = table_order.upper()
    table_line = table_line.upper()
    table_currency = table_currency.upper()

log_data('''Extract partner: %s, last delivery %s, condition: %s, payment: %s, 
    currency: %s, order: %s - %s, currency: %s)''' % (
        table_rubrica, 
        table_extra, 
        table_condition, 
        table_payment,
        table_currency,
        table_order,
        table_line,
        table_currency,
        ), f_log)

# -----------------------------------------------------------------------------
# A. Load active partner (date of delivery)
from_date = (datetime.now() - relativedelta(days=days)).strftime('%Y-%m-%d')
query = '''
    SELECT CKY_CNT FROM %s WHERE 
        DTT_ULT_CONSG >= '%s' AND CKY_CNT >= '2' AND CKY_CNT < '3';
    ''' % (table_extra, from_date)
log_data('Run SQL %s' % query, f_log)

cursor1.execute(query)
user_db = [record['CKY_CNT'] for record in cursor1]

# -----------------------------------------------------------------------------
# B. Currency list
currency_db = {}

query = 'SELECT * FROM %s;' % table_currency
log_data('Run SQL %s' % query, f_log)

cursor2.execute(query)
for record in cursor2:
    ref = record['NKY_VLT']
    currency_db[ref] = record['CDS_VLT']
    # IST_LIT_EURO (sign)
    # CSG_SIMB_VLT (symbol)

# -----------------------------------------------------------------------------
# C. Load bank reference
bank_db = {}

query = 'SELECT * FROM %s WHERE CKY_CNT >= \'2\' AND CKY_CNT < \'3\';' % \
    table_condition
log_data('Run SQL %s' % query, f_log)

cursor2.execute(query)
for record in cursor2:
    bank_db[record['CKY_CNT']] = get_html_bank(record)

# -----------------------------------------------------------------------------
# D. Load partner list
query = 'SELECT * FROM %s WHERE CKY_CNT >= \'2\' AND CKY_CNT < \'3\';' % \
    table_rubrica
log_data('Run SQL %s' % query, f_log)
cursor2.execute(query)

i = 0
f_csv = open(file_csv, 'w')
for record in cursor2:
    try:
        i += 1
        ref = record['CKY_CNT']        
        
        line = u'%s|%s|%s|%s|%s\n' % (
            ref,
            record['CDS_CNT'] or '', # name
            record['CDS_INDIR'] or '', # street
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
file_csv = os.path.join(folder, 'order.csv')
f_csv = open(file_csv, 'w')

log_data('Extract order: %s, detail: %s)' % (table_order, table_line), f_log)

# -----------------------------------------------------------------------------
# A. OC Header
query = 'SELECT * FROM %s WHERE CSG_DOC="OC";' % table_order
log_data('Run SQL %s' % query, f_log)

cursor1.execute(query)
order_db = {}
for record in cursor1:
    key = get_key(record)
    order_db[key] = '%s|%s|%s|%s|%s|%s|%s|%s' % (
        key, 
        record['DTT_DOC'] or '',
        record['CKY_CNT_CLFR'] or '',
        record['CKY_CNT_SPED_ALT'] or '',
        record['NKY_CAUM'] or '',
        record['NKY_PAG'] or '',
        record['CDS_NOTE'] or '',
        currency_db.get(record['NKY_VLT'], ''),
        #record['NKY_CNT_AGENTE'] or '',
        #record['IST_PORTO'] or '',
        )

# -----------------------------------------------------------------------------
# B. OC Line
query = 'SELECT * FROM %s;' % table_line
log_data('Run SQL %s' % query, f_log)

cursor1.execute(query)
for record in cursor1:
    key = get_key(record)
    header = order_db.get(key, '')
    if not header:
        continue # no header order now

    line = '%s|%s|%s|%s|%s|%s|%s|%s|%s|%s\n' % (
        header,
        record['NPR_RIGA'] or '', # pos: 8

        record['DTT_SCAD'] or '',
        record['CKY_ART'] or '',
        record['CDS_VARIAZ_ART'] or '',
        record['NPZ_UNIT'] or '',
        record['NDC_QTA'] or '',
        record['CKY_ART'] or '',
        record['NQT_RIGA_O_PLOR'] or '',
        record['NCF_CONV'] or '',
        )
    f_csv.write(clean_ascii(line))
f_csv.close()

# -----------------------------------------------------------------------------
#                                  END OPERATION:
# -----------------------------------------------------------------------------   
# Publish command:        
import pdb; pdb.set_trace()
log_data('Publish operation: %s' % publish, f_log)
os.system(publish)

# Close open files:
f_log.close()  
sys.exit() # END !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# -----------------------------------------------------------------------------
#                                     TRANSFER: 
# -----------------------------------------------------------------------------   

# Generate key from password:
key = hashlib.sha256(password).digest()
IV = '\x00' * 16 # Empty vector
mode = AES.MODE_CBC
encryptor = AES.new(key, mode, IV=IV)

text = 'j' * 64 + 'i' * 128
ciphertext = encryptor.encrypt(text)
print '\nText: ', text, '\nCipher:', ciphertext

decryptor = AES.new(key, mode, IV=IV)
plain = decryptor.decrypt(ciphertext)
print '\nCipher:', ciphertext, '\nPlain: ', plain        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
