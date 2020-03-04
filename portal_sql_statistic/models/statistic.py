# Copyright 2019  Micronaet SRL (<http://www.micronaet.it>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import io
import xlsxwriter
import logging
import base64
import shutil
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class PivotSaleLine(models.Model):
    """ Model name: ExcelReportFormatPage
    """
    _name = 'pivot.sale.line'
    _description = 'Pivot sale line'
    _order = 'year, date'
    _rec_name = 'product_id'

    # -------------------------------------------------------------------------
    #                                   COLUMNS:
    # -------------------------------------------------------------------------
    # Header:
    year = fields.Integer('Year')
    date = fields.Date('Date')
    document_type = fields.Selection((
         ('BC', 'DDT / Invoice'),
         ('BD', 'Deposit document'),
         ('SL', 'Unload document (prod.)'),
         ('CL', 'Load document (prod.)'),
         ('BF', 'Supplier document'),
         ('BS', 'Unload document'),
         ('RC', 'Refund'),
         ), 'Document type')
    mode = fields.Selection((
         ('sale', 'Sale'),
         ('transport', 'Transport'),
         ('discount', 'Discount'),
         ('fee', 'Fee'),
         ), 'Line mode')
    name = fields.Char('Ref.', size=20)    
    
    partner_id = fields.Many2one('res.partner', 'Partner')
    country_id = fields.Many2one('res.country', 'Country')
    agent_id = fields.Many2one('res.partner', 'Agent')
    salesman_id = fields.Many2one('res.partner', 'Salesman')
    responsible_id = fields.Many2one('res.partner', 'Responsible')
    # TODO Zone

    # Detail:
    product_id = fields.Many2one('product.template', 'Product')
    uom_id = fields.Many2one('product.uom', 'Uom')
    category_id = fields.Many2one('product.category', 'Category')
    
    product_uom_qty = fields.Float('Q.', digits=(16, 3)
    list_price = fields.Float('Price', digits=(16, 3)
    subtotal = fields.Float('Subtotal', digits=(16, 3)

