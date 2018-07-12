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
table_bank = 'con_comm' # TODO

file_csv = os.path.join(folder, 'banck_check.csv')
if mysql['capital']:
    table_bank = table_bank.upper()

print 'Extract bank: %s' % table_bank

# -----------------------------------------------------------------------------
# Load bank information:
# -----------------------------------------------------------------------------
bank_db = {}

query = '''
    SELECT * FROM %s WHERE CKY_CNT >= '2' AND CKY_CNT < '3';
    ''' % table_bank
print 'Run SQL %s' % query

# -------
# Bank 1:
# -------
cursor1.execute(query)
for record in cursor1:
    ref = record['CKY_CNT']
    if ref not in bank_db:
       bank_db[ref] = [
           False, # Anagrafici 
           False, # Bank 1
           False, # Bank 2
           ]
       
    bank_db[ref][1] = record

# -------
# Bank 2:
# -------

# ----------------
# Anagraphic data:
# ----------------

# -------------
# Payment data:
# -------------

# -----------------------------------------------------------------------------
# Write output file:
# -----------------------------------------------------------------------------
i = 0
f_csv = open(file_csv, 'w')

# TODO controlla se serve comunicare altri dati
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
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
