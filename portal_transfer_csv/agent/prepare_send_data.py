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

# -----------------------------------------------------------------------------
# Read configuration parameter:
# -----------------------------------------------------------------------------
cfg_file = os.path.expanduser('./odoo.cfg')
config = ConfigParser.ConfigParser()
config.read([cfg_file])

# -----------------------------------------------------------------------------
# Access database:
# -----------------------------------------------------------------------------
mysql = {
    'hostname': config.get('mysql', 'hostname'),
    'username': config.get('mysql', 'username'),
    'password': config.get('mysql', 'password'),

    'database': config.get('mysql', 'database'),
    'port': eval(config.get('mysql', 'port')),

    'capital': eval(config.get('mysql', 'capital')),
    }

folder = os.path.expanduser(config.get('transfer', 'folder'))
compress = os.path.expanduser(config.get('transfer', 'compress'))
publish = config.get('transfer', 'publish')

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

if mysql['capital']:
    table = table.upper()

# -----------------------------------------------------------------------------
#                                     PARTNER: 
# -----------------------------------------------------------------------------   
table = 'pa_rubr_pdc_clfr'
file_csv = os.path.join(folder, 'partner.csv')


connection = mssql_connect(mysql)
cursor = connection.cursor()

query = '''
    SELECT * 
    FROM %s
    WHERE 
        CKY_CNT >= '2' AND CKY_CNT < '3';
    ''' % table
cursor.execute(query)

i = 0
f_csv = open(file_csv, 'w')
for record in cursor:
    try:
        i += 1
        ref = record['CKY_CNT']        
        
        line = u'%s|%s|%s\n' % (
            ref,             
            record['CDS_CNT'], # name
            record['CDS_INDIR'], # street
            )
        f_csv.write(clean_ascii(line))
    except: 
        print 'Jump line error'
        continue    
        
# -----------------------------------------------------------------------------
#                                     PARTNER: 
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
