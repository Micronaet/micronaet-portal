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

class PortalSaleOrder(orm.Model):
    """ Model name: PortalSaleOrder
    """
    
    _name = 'portal.sale.order'
    _description = 'Portal sale order'
    _rec_name = 'name'
    _order = 'name'

    # Schedule function:
    def schedule_etl_accounting_order(self, cr, uid, fullname, context=None):
        ''' Import procedure
        '''
        import pdb; pdb.set_trace()
        # Pool used:
        line_pool = self.pool.get('portal.sale.order.line')
        partner_pool = self.pool.get('res.partner')

        # Database used:
        order_db = {}
        
        # ---------------------------------------------------------------------
        # Unlink all order and line:
        # ---------------------------------------------------------------------
        line_ids = line_pool.search(cr, uid, [], context=context)
        line_pool.unlink(cr, uid, line_ids, context=context)

        order_ids = self.search(cr, uid, [], context=context)
        self.unlink(cr, uid, order_ids, context=context)
        
        # ---------------------------------------------------------------------
        # Import order and line:
        # ---------------------------------------------------------------------
        tot_col = False
        i = 0        
        for line in open(fullname, 'r'):
            i += 1
            row = line.strip().split('|')
            if tot_col == False:
                tot_col = len(row)
            if len(row) != tot_col:
                _log.error('%s. Different col, jump' % i)
                continue
            
            # -----------------------------------------------------------------
            # Header creation:
            # -----------------------------------------------------------------
            key = row[0]
            partner_ref = row[2]
            address_ref = row[3] # TODO
            
            partner_ids = partner_pool.search(cr, uid, [
                ('ref', '=', partner_ref),
                ], context=context)
            if not partner_ids:
                _logger.error('Partner ref. not found, no import: %s' % \
                    partner_ref)
                continue
                
            header = {
                'name': key,
                'date': row[1],
                'partner_id': partner_ids[0],
                'note': row[6],                
                }
            if key not in order_db:
                order_db[key] = self.create(cr, uid, header, context=context)
            order_id = order_db[key]    
            
            # -----------------------------------------------------------------
            # Line creation:
            # -----------------------------------------------------------------
            data = {
                'order_id': order_id,

                'sequence': row[7],  
                'deadline': row[8],
                'name': row[10],
                'quantity': row[13],
                'unit_price': row[11],
                'subtotal': 0.0
                }
            line_pool.create(cr, uid, data, context=context)            
        return True
        
    _columns = {
        'sequence': fields.char('Seq.', size=4), 
        'name': fields.char('Number', size=64, required=True), 
        'date': fields.date('Date'),
        'deadline': fields.date('Dateline'),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'user_id': fields.many2one('res.users', 'User'),
        'total': fields.float('Total', digits=(16, 3)),
        'note': fields.text('Note'),
        }

class PortalSaleOrderLine(orm.Model):
    """ Model name: Portal Sale Order Line
    """
    
    _name = 'portal.sale.order.line'
    _description = 'Portal sale order line'
    _rec_name = 'name'
    _order = 'name'
    
    _columns = {
        'name': fields.char('Number', size=64, required=True),
        'deadline': fields.date('Deadline'),
        'quantity': fields.float('Q.', digits=(16, 3)),
        'unit_price': fields.float('Price', digits=(16, 3)),
        'subtotal': fields.float('Subtotal', digits=(16, 3)),
        'order_id': fields.many2one('portal.sale.order', 'Order'),
        }
       
class PortalSaleOrder(orm.Model):
    """ Add relation fields:
    """
    
    _inherit = 'portal.sale.order'

    _columns = {
        'line_ids': fields.one2many(
            'portal.sale.order.line', 'order_id', 'Line'),
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
