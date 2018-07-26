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
import openerp
import logging
from openerp import models, fields, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp.tools.translate import _
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare,
    )


_logger = logging.getLogger(__name__)

class PortalSaleOrder(models.Model):
    """ Model name: PortalSaleOrder
    """
    
    _name = 'portal.sale.order'
    _description = 'Portal sale order'
    _rec_name = 'name'
    _order = 'name'

    # -------------------------------------------------------------------------
    # Schedule function:
    # -------------------------------------------------------------------------
    @api.model
    def schedule_etl_accounting_order(self, fullname):
        ''' Import procedure
        '''
        # Pool used:
        line_pool = self.env['portal.sale.order.line']
        partner_pool = self.env['res.partner']
        user_pool = self.env['res.users']

        # Database used:
        order_db = {}
        
        # ---------------------------------------------------------------------
        # Unlink all order and line:
        # ---------------------------------------------------------------------
        lines = line_pool.search([])
        lines.unlink()

        orders = self.search([])
        orders.unlink()
        
        # ---------------------------------------------------------------------
        # Import order and line:
        # ---------------------------------------------------------------------
        tot_col = False
        i = 0        
        for line in open(fullname, 'r'):
            i += 1
            if i == 10: # XXX remove
                import pdb; pdb.set_trace()
            try:
                row = line.strip().split('|')
                if tot_col == False:
                    tot_col = len(row)
                if len(row) != tot_col:
                    _logger.error('%s. Different col, jump' % i)
                    continue
                
                # -------------------------------------------------------------
                # Header creation:
                # -------------------------------------------------------------
                # Fields:
                key = row[0]
                partner_ref = row[2]
                address_ref = row[3] # TODO
                
                if not partner_ref:
                    _logger.error('Partner ref. not found, no import!')
                    continue
                partners = partner_pool.search([('ref', '=', partner_ref)])
                if not partners:
                    _logger.error('Partner ref. not found, no import: %s' % \
                        partner_ref)
                    continue

                users = user_pool.search([('login', '=', partner_ref)])
                if not users:
                    _logger.error('User login ref. not found, no import: %s' %\
                        partner_ref)
                    continue
                    
                header = {
                    'name': key,
                    'date': row[1],
                    'partner_id': partners[0].id,
                    'user_id': users[0].id,
                    'note': row[6],                
                    }
                if key not in order_db:
                    order_db[key] = self.create(header).id
                order_id = order_db[key]
                
                # -------------------------------------------------------------
                # Line creation:
                # -------------------------------------------------------------
                # Fields:
                quantity = float(row[15])
                unit_price = float(row[12])
                
                data = {
                    'order_id': order_id,

                    'sequence': row[7],  
                    'deadline': row[8],
                    'name': row[10],
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'subtotal': quantity * unit_price,
                    }
                line_pool.create(data)
            except:
                _logger.error('%s. General error on line' % i)
                continue    
        return True
        
    # -------------------------------------------------------------------------
    #                               COLUMNS:    
    # -------------------------------------------------------------------------
    name = fields.Char('Number', size=64, required=True)
    date = fields.Date('Date')
    deadline = fields.Date('Dateline')
    partner_id = fields.Many2one('res.partner', 'Partner')
    user_id = fields.Many2one('res.users', 'User')
    total = fields.Float('Total', digits=(16, 3))
    note = fields.Text('Note')
    # -------------------------------------------------------------------------

class PortalSaleOrderLine(models.Model):
    """ Model name: Portal Sale Order Line
    """
    
    _name = 'portal.sale.order.line'
    _description = 'Portal sale order line'
    _rec_name = 'name'
    _order = 'name'
    
    # -------------------------------------------------------------------------
    #                               COLUMNS:    
    # -------------------------------------------------------------------------
    sequence = fields.Char('Seq.', size=4)
    name = fields.Char('Number', size=64, required=True)
    deadline = fields.Date('Deadline')
    quantity = fields.Float('Q.', digits=(16, 3))
    unit_price = fields.Float('Price', digits=(16, 3))
    subtotal = fields.Float('Subtotal', digits=(16, 3))
    order_id = fields.Many2one('portal.sale.order', 'Order')
    # -------------------------------------------------------------------------
       
class PortalSaleOrder(models.Model):
    """ Add relation fields:
    """
    
    _inherit = 'portal.sale.order'

    # -------------------------------------------------------------------------
    #                               COLUMNS:    
    # -------------------------------------------------------------------------
    line_ids = fields.One2many('portal.sale.order.line', 'order_id', 'Line')
    # -------------------------------------------------------------------------
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
