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
from odoo import models, fields, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools.translate import _
from odoo.tools import (
    DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare,
    )


_logger = logging.getLogger(__name__)

class PortalDeadline(models.Model):
    ''' Porta deadline data obj
    '''
    _name = 'portal.deadline'
    _description = 'Payment deadline'
    _order='name,deadline' 

    # -----------------------------------------------------------------------------
    # Utility function:
    # -----------------------------------------------------------------------------
    # Conversion function:
    @api.model
    def clean(self, value):  
        ''' ASCII Problem conversion
        '''
        value = value.decode('cp1252')
        value = value.encode('utf-8')
        return value.strip()

    @api.model
    def format_date(self, value):
        ''' Format data value
        '''
        value = value.strip()
        if len(value)==8:
           if value:
              return value[:4] + '-' + value[4:6] + '-' + value[6:8]
        return False

    @api.model
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
    @api.model
    def schedule_etl_accounting_deadline(self, fullname, verbose=True):
        ''' Import deadline from accounting
        '''
        partner_pool = self.env['res.partner']
        tot_col = 0
        old_order_ref = ''
        try: 
            file_input = os.path.join(os.path.expanduser(fullname))
            rows = open(file_input, 'rb') 
        except:
            _logger.error('Problem open file: [%s, %s]' % (path, file_name))
            return
        
        # Remove all previous
        deadlines = self.search([]) 
        deadlines.unlink()

        for row in rows:
            try:
                line=row.split(';')
                if tot_col == 0:
                   tot_col = len(line)
                   _logger.info(
                       'Start import [%s] Cols: %s' % (file_input, tot_col))
                   
                if not (len(line) and (tot_col==len(line))):
                    _logger.error(
                        'Empty line or cols [Org: %s - This %s]' % (
                            tot_col, len(line)))
                    continue

                try: # master error:
                    partner_ref = self.clean(line[0])
                    deadline = self.format_date(line[1])
                    total = self.format_float(line[2]) 
                    payment = self.clean(line[3]).lower()
                    invoice = self.clean(line[4])
                    date = self.format_date(line[5])
                    currency = self.clean(line[6])
                    
                    if partner_ref[:1] == '4':
                        continue # XXX no supplier data
                    elif partner_ref[:1] == '2': # Customer
                        pass
                    else:    
                        _logger.error(
                            'Cannot find c/s from code: %s' % partner_ref)
                        continue
                     
                    # Calculated field:                   
                    if total > 0:
                       total_in = total   # AVERE
                       total_out = 0.0
                    else:
                       total_in = 0.0
                       total_out = -total # DARE

 
                    partners = partner_pool.search([
                        ('ref', '=', partner_ref),
                        ])
                     
                    if not partners:
                       _logger.error('Not found: %s' % partner_ref)
                       continue
                       
                    partner = partners[0]
                    data = {
                        'name': '%s [%s]: %s (%s EUR)' % (
                            partner.name, 
                            partner_ref, 
                            deadline, 
                            total,
                            ),
                        'partner_id': partner.id,
                        'user_id': partner.portal_user_id.id,
                        'deadline': deadline,
                        'date': date,
                        'invoice': invoice,
                        'currency': currency,
                        'total': total,
                        'total_in': total_in,
                        'total_out': total_out, # XXX needed?
                        'payment': payment,
                        }                          
                    try:
                        self.create(data)
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

    # -------------------------------------------------------------------------
    #                                    COLUMNS:
    # -------------------------------------------------------------------------
    name = fields.Char('Deadline', size=80, required=True)
    partner_id = fields.Many2one('res.partner', 'Label')
    user_id = fields.Many2one('res.users', 'User')
    date = fields.Date('Date')
    deadline = fields.Date('Deadline')
    invoice = fields.Char('Invoice', size=30)
    total = fields.Float('Amount', digits=(16, 2))
    total_in = fields.Float('IN', digits=(16, 2))
    total_out = fields.Float('OUT', digits=(16, 2))
    currency = fields.Char('Currency', size=25)
    payment = fields.Selection([
        ('b', 'Bonifico'),            
        ('c', 'Contanti'),            
        ('r', 'RIBA'),            
        ('t', 'Tratta'),            
        ('m', 'Rimessa diretta'),            
        ('x', 'Rimessa diretta X'),
        ('y', 'Rimessa diretta Y'),            
        ('z', 'Rimessa diretta Z'),            
        ('v', 'MAV'),            
        ], 'Type')
    # -------------------------------------------------------------------------
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
