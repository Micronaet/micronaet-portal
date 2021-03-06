# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2001-2018 Micronaet SRL (<https://micronaet.com>).
#
#    This program is free software: you can redistribute it and / or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import os
import sys
import logging
import openerp
from openerp import models, fields
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

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
