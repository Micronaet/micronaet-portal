# Copyright 2019  Micronaet SRL (<http://www.micronaet.it>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields, api
# import io
# import xlsxwriter
# import base64
# import shutil

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """ Model update with extra fields
    """
    _inherit = 'res.partner'

    # Columns:
    account_ref = fields.Char(string='Account ref.', size=9)
    country_code = fields.Char(string='Country code', size=4)
    pivot_partner = fields.Boolean(string='Pivot partner')

    agent_id = fields.Many2one('res.partner', 'Agent')
    salesman_id = fields.Many2one('res.partner', 'Salesman')
    responsible_id = fields.Many2one('res.partner', 'Responsible')

    # TODO put also in statistic
    account_mode = fields.Selection([
        ('I', 'Italy'),
        ('R', 'Vatican'),
        ('E', 'Extra CEE'),
        ('C', 'CEE'),
        ], 'Account_mode')


class ProductTemplate(models.Model):
    """ Model update with extra fields
    """
    _inherit = 'product.template'

    # Columns:
    pivot_product = fields.Boolean(string='Pivot product')


class PivotCurrency(models.Model):
    """ Model name: Currency
    """
    _name = 'pivot.currency'
    _description = 'Currency'

    name = fields.Char('Currency', size=40)
    symbol = fields.Char('Symbol', size=10)
    account_ref = fields.Integer('Account ref')


class PivotSaleReason(models.Model):
    """ Model name: ExcelReportFormatPage
    """
    _name = 'pivot.sale.reason'
    _description = 'Reason'

    name = fields.Char('Sale reason', size=40)
    account_ref = fields.Integer('Account ref')
    stats_used = fields.Boolean(
        'Used', help='Used in stat (filter only active stats)')


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
    year = fields.Integer('Year', required=True)
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
    currency_id = fields.Many2one('pivot.currency', 'Currency')
    reason_id = fields.Many2one('pivot.sale.reason', 'Reason')

    # Partner related fields:
    country_id = fields.Many2one(
        'res.country', 'Country', related='partner_id.country_id',
        store=True)
    agent_id = fields.Many2one(
        'res.partner', 'Agent', related='partner_id.agent_id',
        store=True)
    salesman_id = fields.Many2one(
        'res.partner', 'Salesman', related='partner_id.salesman_id',
        store=True)
    responsible_id = fields.Many2one(
        'res.partner', 'Responsible', related='partner_id.responsible_id',
        store=True)

    # TODO Zone
    # TODO product_code, customer_code to automatic link partner and product

    # Detail:
    product_id = fields.Many2one('product.template', 'Product')

    # Product related
    category_id = fields.Many2one(
        'product.category', 'Category',
        related='product_id.categ_id', store=True)
    uom_id = fields.Many2one(
        'product.uom', 'Uom',
        related='product_id.uom_id', store=True)

    product_uom_qty = fields.Float('Q.', digits=(16, 3))
    list_price = fields.Float('Price', digits=(16, 3))
    subtotal = fields.Float('Subtotal', digits=(16, 3))
    currency_subtotal = fields.Float(
        'Currency Subtotal', digits=(16, 3),
        help='Real document total in currency value (not to be used)')
