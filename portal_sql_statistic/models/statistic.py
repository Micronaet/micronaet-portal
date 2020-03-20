# Copyright 2019  Micronaet SRL (<http://www.micronaet.it>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import os
import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    """ Add reference for user
    """
    _inherit = 'res.users'

    stat_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Stat Partner')


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


class PivotCurrency(models.Model):
    """ Model name: Currency
    """
    _name = 'pivot.currency'
    _description = 'Currency'

    # Columns:
    name = fields.Char('Currency', size=40)
    symbol = fields.Char('Symbol', size=10)
    account_ref = fields.Integer('Account ref')


class PivotYear(models.Model):
    """ Model name: Years
    """
    _name = 'pivot.year'
    _description = 'Year'

    @api.multi
    def reload_year(self):
        """ Reload this year
        """
        path = '~/data'

        # Load from pickle file
        fullname = os.path.join(
            os.path.expanduser(path),
            self.filename
            )
        if not os.path.isfile(fullname):
            raise exceptions.Error('No file: %s' % fullname)
            return False
        # self.remove_year()
        # TODO complete here!
        return True

    @api.multi
    def remove_year(self):
        """ Remove this year
        """
        line_pool = self.env['pivot.sale.line']
        return line_pool.search([
            ('year', '=', self.name),
            ]).unlink()

    name = fields.Integer('Year', required=True)
    filename = fields.Char('Filename', size=20)
    load = fields.Boolean('Load', help='Load always this year')


class PivotSaleReason(models.Model):
    """ Model name: ExcelReportFormatPage
    """
    _name = 'pivot.sale.reason'
    _description = 'Reason'

    name = fields.Char('Sale reason', size=40)
    account_ref = fields.Integer('Account ref')
    stats_used = fields.Boolean(
        'Used', help='Filter enabled when need exclusion in sale stats',
        default=True)


class PivotProductSector(models.Model):
    """ Model name: Product statistic sector
    """
    _name = 'pivot.product.sector'
    _description = 'Statistic category'

    name = fields.Char('Sector', size=40, required=True)
    account_ref = fields.Char('Account ref', size=2)


class PivotProductStatistic(models.Model):
    """ Model name: Product statistic category
    """
    _name = 'pivot.product.statistic'
    _description = 'Statistic category'

    name = fields.Char('Statistic category', size=40)
    account_ref = fields.Char('Account ref', size=4)
    sector_id = fields.Many2one(
        comodel_name='pivot.product.sector', string='Sector')


class PivotProductSectorRelations(models.Model):
    """ Model name: Product statistic sector
    """
    _inherit = 'pivot.product.sector'

    statistic_ids = fields.One2many(
        comodel_name='pivot.product.statistic', inverse_name='sector_id',
        string='Statistic category')


class PivotSaleLine(models.Model):
    """ Model name: ExcelReportFormatPage
    """
    _name = 'pivot.sale.line'
    _description = 'Pivot sale line'
    _order = 'year, date'
    _rec_name = 'product_id'

    @api.model
    def salesman_domain_filter(self):
        """ Server Action for pre filter
        """
        # model_pool = self.env['ir.model.data']
        pivot_view_id = tree_view_id = False
        user = self.env['res.users'].browse(self.env.uid)
        partner_id = user.stat_partner_id.id
        domain = [
            '&',
            ('document_type', 'in', ('BC', 'RC')),
            '|', '|',
            ('agent_id', '=', partner_id),
            ('salesman_id', '=', partner_id),
            ('responsible_id', '=', partner_id),
        ]
        _logger.warning('My Domain: %s' % (domain))
        return {
            'type': 'ir.actions.act_window',
            'name': 'Statistic',
            'view_type': 'form',
            'view_mode': 'pivot,tree',
            # 'res_id': 1,
            'res_model': 'pivot.sale.line',
            'view_id': pivot_view_id,
            'views': [(pivot_view_id, 'pivot'), (tree_view_id, 'tree')],
            'domain': domain,
            'context': {'search_default_exclude_reason': True},
            # self.env.context,
            'target': 'current',
            'nodestroy': False,
        }

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
         ('RC', 'Customer Refund'),
         ('RF', 'Supplier Refund'),
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
    sector_id = fields.Many2one(
        'pivot.product.sector', 'Sector',
        related='product_id.sector_id', store=True)
    statistic_id = fields.Many2one(
        'pivot.product.statistic', 'Statistic',
        related='product_id.statistic_id', store=True)
    category_id = fields.Many2one(
        'product.category', 'Category',
        related='product_id.categ_id', store=True)
    uom_id = fields.Many2one(
        'product.uom', 'Uom',
        related='product_id.uom_id', store=True)

    product_uom_qty = fields.Float('Q.', digits=(16, 3))
    list_price = fields.Float('Price', digits=(16, 3))
    subtotal = fields.Float('Subtotal', digits=(16, 3))
    exchange = fields.Float('Exchange', digits=(16, 3))
    currency_subtotal = fields.Float(
        'Currency Subtotal', digits=(16, 3),
        help='Real document total in currency value (not to be used)')


class ProductTemplate(models.Model):
    """ Model update with extra fields
    """
    _inherit = 'product.template'

    # Columns:
    pivot_product = fields.Boolean('Pivot product')
    sector_id = fields.Many2one('pivot.product.sector', 'Sector')
    statistic_id = fields.Many2one('pivot.product.statistic', 'Statistic')
