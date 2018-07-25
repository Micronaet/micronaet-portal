#!/usr/bin/python
# -*- coding: utf-8 -*-
###############################################################################
#
# ODOO (ex OpenERP) 
# Open Source Management Solution
# Copyright (C) 2001-2018 Micronaet S.r.l. (<https://micronaet.com>)
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
import string
import random
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

class ResUsers(models.Model):
    """ Model name: ResPartner
    """
    
    _inherit = 'res.users'
    
    # -------------------------------------------------------------------------
    # Columns:
    # -------------------------------------------------------------------------
    first_password = fields.char('First password', size=25)

class ResPartner(models.Model):
    """ Model name: ResPartner
    """
    
    _inherit = 'res.partner'
    
    # -------------------------------------------------------------------------
    #                     UTILITY (XMLRPC procedure):
    # -------------------------------------------------------------------------
    @api.multi
    def create_portal_user(self, update=False):
        ''' Create porta user for partner passed:
        '''
        def get_random_password(size):
            ''' Generate random password take elements in lower upper number
                and some random chars
                Max length is size
            '''
            origin = '%s%s%s%s' % (
                string.ascii_letters, # lower letters
                string.ascii_letters.upper(), # upper letters
                string.digits, # numbers
                u'!@#_-$%', # extra char
            return ''.join(random.choise(origin) for i in range(size))
        
        user_pool = self.env['res.users']
        update_list = [] # (partner, user_id)
        
        # Create user for partner who doesn't have:
        for partner in self:
            ref = partner.ref
            if not ref:
                # No ref no user creation:
                _logger.warning('No user without ref: %s' % partner.id)
                continue
            if partner.portal_user_id:
                continue # yet present
            
            users = user_pool.search([('login', '=', partner.ref)])
            data = {
                'active': True,
                'login': ref,
                #'password': 'secret%s' % ref,
                'partner_id': partner.id,
                #'name': 'User: %s' % partner.name,
                'signature': partner.name,                
                }        
            if users:
                # TODO manage multiple
                if update: 
                    users.write(data)
                user_id = users[0].id
            else:
                # Generate random password when creating:
                password = get_random_password(10)
                data['password'] = password
                data['first_password'] = password
                
                user_id = user_pool.create(data)
            update_list.append((partner, user_id))    
        
        # Update portal user for partner:
        for partner, user_id in update_list:
            partner.write({'portal_user_id': user_id, })
        return True
        
    # -------------------------------------------------------------------------
    # Scheduled import operation:
    # -------------------------------------------------------------------------
    @api.model
    def import_csv_partner_data(self, filename, user_creation=False):
        ''' Import filename for partner creation (and users too)
        '''
        _logger.info('Update partner user, creation = %s' % user_creation)
        partner_user_ids = []
        max_col = False

        i = 0
        for line in open(filename):
            i += 1
            if i % 100 == 0:
                _logger.info('Reading row: %s ' % i)
                
            row = (line.strip()).split('|')
            if max_col == False:
                max_col = len(row)
            if len(row) != max_col:
                _logger.error('Different col: %s' % line)
                continue
                    
            ref = row[0]
            name = row[1]
            street = row[2]
            create_user = row[3] == 'X'
            portal_payment = row[4]
            
            partners = self.search([('ref', '=', ref)])
            data = {
                'ref': ref,
                'active': True,
                'is_company': True,
                'name': name,
                'street': street,
                'portal_payment': portal_payment,
                # portal_user_id:       
                }
            if partners: 
                # TODO multiple management
                partner = partners[0]
                partner_user_ids.append(partner)
                partners.write(data)
            else:
                partner = self.create(data)
                partner_user_ids.append(partner)
                
            break # TODO remove
            
        if user_creation:
            _logger.info('Update user')
            self.create_portal_user(partner_user_ids)
        return [p.id for p in partner_user_ids]    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
