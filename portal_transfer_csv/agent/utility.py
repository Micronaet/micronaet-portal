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
import shutil
import ConfigParser

# MySQL access:
import MySQLdb
import MySQLdb.cursors

# Utility:
import string
import random
from datetime import datetime, timedelta

# Crypto library:
#import hashlib
#from Crypto.Cipher import AES

# -----------------------------------------------------------------------------
#                                UTILITY FUNCTION:
# -----------------------------------------------------------------------------   
def get_random_password(size):
    ''' Generate random password take elements in lower upper number
        and some random chars
        Max length is size
    '''
    mask = '%s' * 6
    origin = mask % (
        string.ascii_letters, # lower letters
        string.digits, # numbers
        u'!@#_-$%', # extra char
        
        string.ascii_letters.upper(), # upper letters                
        string.digits, # numbers
        u'!@#_-$%', # extra char
        )
    return ''.join(random.choice(origin) for i in range(size))
            
# SQL Connection function:
def mssql_check_export(mysql):
    ''' Check status of export in database
    '''
    # Check file:
    f_log = open(mysql['check_file'], 'r')
    check_list = mysql['check_list']
    
    error = ''
    i = 0
    for line in f_log:
        i += 1
        line = line.strip().split('|')
        
        # ---------------------------------------------------------------------
        # Line format check:
        # ---------------------------------------------------------------------
        if len(line) != 3:
            error += '%s. Line not correct\n' % i
            continue # jump line not correct

        date = line[0].strip()
        table = line[1].strip()
        esit = line[2].strip()
        
        # ---------------------------------------------------------------------
        # Table esit:
        # ---------------------------------------------------------------------
        if esit != '0':
            error += '%s. Table %s negative export esit: %s\n' % (
                i, table, esit)                
            continue # jump line not correct
            
        # ---------------------------------------------------------------------
        # Date check:
        # ---------------------------------------------------------------------
        # TODO Date check
        
        # ---------------------------------------------------------------------
        # Table check list:
        # ---------------------------------------------------------------------
        if table in check_list:
            check_list.remove(table)
        else:
            error += '%s. Table %s not in check list\n' % (i, table)
            continue # jump line not correct
            
    # -------------------------------------------------------------------------
    # Table check list remain:
    # -------------------------------------------------------------------------
    if check_list: # not all table removed
        error += 'Table not exported on database [%s]\n' % check_list
    
    if error: 
        error = 'Database check: %s\n%s' % (mysql['database'], error, )
    return error

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
    message = '%s [%s] %s%s' % (
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
    mask = '<p><b>Bank: </b>%s<br/><b>IBAN code: </b>%s<br/>' + \
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
        
'''def crypt_text(text):
    # -------------------------------------------------------------------------
    #                                ENCRYPTO TRANSFER: 
    # -------------------------------------------------------------------------
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
'''
