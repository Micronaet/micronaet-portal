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

class ResPartner(orm.Model):
    """ Model name: ResPartner
    """
    
    _inherit = 'res.partner'
    
    # -------------------------------------------------------------------------
    # Utility:
    # -------------------------------------------------------------------------
    def create_portal_user(self, cr, uid, ids, update=False, context=None):
        ''' Create porta user for partner passed:
        '''
        user_pool = self.pool.get('res.users')
        update_list = [] # (partner_id, user_id)
        
        # Create user for partner who doesn't have:
        for partner in self.browse(cr, uid, ids, context=context):
            ref = partner.ref
            if not ref:
                # No ref no user creation:
                _logger.warning('No user without ref: %s' % partner.id)
                continue
            if partner.portal_user_id:
                continue # yet present
            
            user_ids = user_pool.search(cr, uid, [
                ('login', '=', partner.ref),
                ], context=context)
            data = {
                'active': True,
                'login': ref,
                'password': 'secret%s' % ref,
                'partner_id': partner.id,
                #'name': 'User: %s' % partner.name,
                'signature': partner.name,                
                }        
            if user_ids:
                # TODO manage multiple
                if update: 
                    user_pool.write(cr, uid, user_ids, data, context=context)
                user_id = user_ids[0]    
            else:
                user_id = user_pool.create(cr, uid, data, context=context)
            update_list.append((partner.id, user_id))    
        
        # Update portal user for partner:
        for partner_id, user_id in update_list:
            self.write(cr, uid, partner_id, {
                'portal_user_id': user_id,
                }, context=context)                    
        return True
        
    # -------------------------------------------------------------------------
    # Scheduled import operation:
    # -------------------------------------------------------------------------
    def import_csv_partner_data(self, cr, uid, filename, user_creation=False,
            context=None):
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
            
            partner_ids = self.search(cr, uid, [
                ('ref', '=', ref),
                ], context=context)
            data = {
                'ref': ref,
                'active': True,
                'is_company': True,
                'name': name,
                'street': street,
                'portal_payment': portal_payment,
                # portal_user_id:                    
                }    
            if partner_ids: 
                # TODO multiple management
                partner_user_ids.append(partner_ids[0])
                partner_id = self.write(
                    cr, uid, partner_ids, data, context=context)
            else:
                partner_id = self.create(cr, uid, data, context=context)
                partner_user_ids.append(partner_id)
                
        if user_creation:
            _logger.info('Update user')
            self.create_portal_user(
                cr, uid, partner_user_ids, context=context)
        return partner_user_ids            
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
