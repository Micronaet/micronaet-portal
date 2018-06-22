# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import os
import sys
import logging
import openerp
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)

_logger = logging.getLogger(__name__)


class PortalDeadline(osv.osv):
    ''' Porta deadline data obj
    '''
    _name = 'portal.deadline'
    _description = 'Payment deadline'
    _order='name,deadline' 

    # -----------------------------------------------------------------------------
    # Utility function:
    # -----------------------------------------------------------------------------
    # Conversion function:
    def clean(self, value):  
        ''' ASCII Problem conversion
        '''
        value = value.decode('cp1252')
        value = value.encode('utf-8')
        return value.strip()

    def format_date(self, value):
        ''' Format data value
        '''
        value = value.strip()
        if len(value)==8:
           if value:
              return value[:4] + '-' + value[4:6] + '-' + value[6:8]
        return False

    def format_float(self, value):
        ''' Format float value
        '''
        value = value.strip() 
        if value:
           return float(value.replace(',', '.'))
        else:
           return 0.0

    # -------------------------------------------------------------------------
    # Scheduled action: 
    # -------------------------------------------------------------------------
    def schedule_etl_accounting_deadline(
            self, cr, uid, fullname, verbose=True, context=None):
        ''' Import deadline from accounting
        '''
        partner_pool = self.pool.get('res.partner')
        tot_col = 0
        old_order_ref = ''
        try: 
            file_input=os.path.join(os.path.expanduser(fullname))
            rows = open(file_input, 'rb') 
        except:
            _logger.error('Problem open file: [%s, %s]' % (path, file_name))
            return
        
        # Remove all previous
        deadline_ids = self.search(cr, uid, [], context=context) 
        self.unlink(cr, uid, deadline_ids, context=context) 
        for row in rows:
            try:
                line=row.split(';')
                if tot_col == 0:
                   tot_col = len(line)
                   _logger.info(
                       'Start import [%s] Cols: %s' % (file_input, tot_col,))
                   
                if not (len(line) and (tot_col==len(line))):
                    _logger.error(
                        'Empty line or cols [Org: %s - This %s]' % (
                            tot_col, len(line)))
                    continue

                try: # master error:
                    partner_ref = self.clean(line[0])
                    deadline = self.format_date(line[1])
                    total = self.format_float(line[2]) 
                    type_id = self.clean(line[3]).lower()
                    invoice = self.clean(line[4])
                    date = self.format_date(line[5])
                    currency = self.clean(line[6])
                    
                    if partner_ref[:1] == '4':
                        continue # XXX no supplier data
                    elif partner_ref[:1] == "2": # Customer
                        pass
                    else:    
                        _logger.error(
                            'Cannot find c/s from code: %s' % (
                                partner_ref, ))
                        continue
                     
                    # Calculated field:                   
                    if total > 0:
                       total_in = total   # AVERE
                       total_out = 0.0
                    else:
                       total_in = 0.0
                       total_out = -total # DARE

 
                    partner_ids = partner_pool.search(cr, uid, [
                        ('ref', '=', partner_ref),
                        ], context=context)
                     
                    if not partner_ids:
                       _logger.error('Not found: %s' % partner_ref)
                       continue
                    partner_proxy = partner_pool.browse(
                        cr, uid, partner_ids, context=context)[0]
                    data = {
                        'name': '%s [%s]: %s (%s EUR)' % (
                            partner_proxy.name, 
                            partner_ref, 
                            deadline, total),
                        'partner_id': partner_proxy.id,
                        'user_id': partner_proxy.portal_user_id.id,
                        'deadline': deadline,
                        'date': date,
                        'invoice': invoice,
                        'currency': currency,
                        'total': total,
                        'in': total_in,
                        'out': total_out, # XXX needed?
                        'type': type_id,
                        }                          
                    try:
                        self.create(cr, uid, data, context=context)
                        if verbose: 
                            _logger.info('Deadline insert')
                    except:
                       _logger.error('Error creating deadline')
                except:
                    _logger.error('Generic error import this line')
            except:
                _logger.error('Generic error!')
        _logger.info('End importation deadline')
        return True
    
    _columns = {
        'name': fields.char('Deadline', size=80),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'user_id': fields.many2one('res.users', 'User'),
        'date': fields.date('Date'),
        'deadline': fields.date('Deadline'),
        'invoice': fields.char('Invoice', size=30),
        'total': fields.float('Amount', digits=(16, 2)),
        'in': fields.float('IN', digits=(16, 2)),
        'out': fields.float('OUT', digits=(16, 2)),
        'currency': fields.char('Currency', size=25),
        'type': fields.selection([
            ('b', 'Bonifico'),            
            ('c', 'Contanti'),            
            ('r', 'RIBA'),            
            ('t', 'Tratta'),            
            ('m', 'Rimessa diretta'),            
            ('x', 'Rimessa diretta X'),
            ('y', 'Rimessa diretta Y'),            
            ('z', 'Rimessa diretta Z'),            
            ('v', 'MAV'),            
            ], 'Type', select=True),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
