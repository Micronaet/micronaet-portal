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
from datetime import datetime, timedelta

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

