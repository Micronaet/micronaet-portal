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

# -----------------------------------------------------------------------------
#                                      START: 
# -----------------------------------------------------------------------------   
print 'Start payment check procedure'

connection1 = mssql_connect(mysql1)
cursor1 = connection1.cursor()
print  'Connect with MySQL1 database: %s' % connection1

connection2 = mssql_connect(mysql2)
cursor2 = connection2.cursor()
print  'Connect with MySQL2 database: %s' % connection2

# -----------------------------------------------------------------------------
#                                       BANK: 
# -----------------------------------------------------------------------------   
table_bank = 'pc_condizioni_comm'
table_partner = 'pa_rubr_pdc_clfr'
table_payment = 'cp_pagamenti'
table_currency = 'mu_valute'

if mysql1['capital']:
    table_bank = table_bank.upper()
    table_partner = table_partner.upper()
    table_payment = table_payment.upper()
    table_currency = table_currency.upper()
print 'Table used: Bank: %s, Partner: %s, Payment: %s, Currency: %s ' % (
    table_bank, table_partner, table_payment, table_currency)

# -----------------------------------------------------------------------------
# Load bank information:
# -----------------------------------------------------------------------------
bank_db = {}

# -------------
# Bank 1 and 2:
# -------------
query = '''
    SELECT CC.*, P.*
    FROM 
        %s CC LEFT JOIN %s P ON (CC.NKY_PAG=P.NKY_PAG) 
    WHERE 
        CC.CKY_CNT >= '2' AND CC.CKY_CNT < '3';
    ''' % (table_bank, table_payment)
print 'Run SQL %s' % query

for cursor, position in ((cursor1, 1), (cursor2, 2)):
    cursor.execute(query)
    for record in cursor:
        ref = record['CKY_CNT']
        if ref not in bank_db:
           bank_db[ref] = [
               '', # Anagrafici 
               '', # Bank 1
               '', # Bank 2
               ]
        bank_db[ref][position] = record

# ----------------
# Anagraphic data:
# ----------------
query = 'SELECT * FROM %s WHERE CKY_CNT >= \'2\' AND CKY_CNT < \'3\';' % \
    table_partner
print 'Run SQL %s' % query

cursor2.execute(query) # XXX better DB 1?
for record in cursor2:
    ref = record['CKY_CNT']
    if ref in bank_db:
        bank_db[ref][0] = record

# ---------
# Currency:
# ---------
currency_db = {}
query = 'SELECT * FROM %s;' % table_currency
print 'Run SQL %s' % query

cursor2.execute(query)
for record in cursor2:
    ref = record['NKY_VLT']
    currency_db[ref] = record['CDS_VLT']

# -----------------------------------------------------------------------------
# Write output file:
# -----------------------------------------------------------------------------
import pdb; pdb.set_trace()
i = 0
file_csv = os.path.join(folder, 'bank_check.csv')
f_csv = open(file_csv, 'w')

# TODO controlla se serve comunicare altri dati
f_csv.write(
    'Stato|Conto|Ragione sociale|Paese|Pagamento|Valuta'
    '|Banca 1|IBAN1|BIC1'
    '|Banca 2|IBAN2|BIC2\n'
    )
for ref in bank_db:
    (partner, bank1, bank2) = bank_db[ref]
    
    try:
        i += 1

        iban1 = bank1['CSG_IBAN_BBAN']
        iban2 = bank2['CSG_IBAN_BBAN']        
        
        payment = bank2['CDS_PAG'] # XXX status of payment
        
        currency = currency_db.get(bank2['NKY_VLT'], '') # XXX Used Bank 2

        status = '' # XXX test for check status
        if iban1 and iban1 != iban2:
            status = 'IBAN' # Different IBAN

        line = '%s|' * 12 + '\n' % (
            status,
            ref,
            partner['CDS_RAGSOC_COGN'] or partner['CDS_CNT'],
            partner['CDS_LOC'],
            payment,
            currency,
            bank1['CDS_BANCA'],
            iban1,
            bank1['CSG_BIC'],
            bank2['CDS_BANCA'],
            iban2,
            bank2['CSG_BIC'], 
            )
        
        f_csv.write(clean_ascii(line))
    except: 
        print 'Jump line error'
        continue    
f_csv.close()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
