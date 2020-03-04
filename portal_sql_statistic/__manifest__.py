# Copyright 2019  Micronaet SRL (<http://www.micronaet.it>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Portal Statistic',
    'version': '11.0.2.0.0',
    'category': 'Statistic',
    'description': '''
        Statistic from SQL in ODOO
        ''',
    'summary': 'Excel, utility, report',
    'author': 'Micronaet S.r.l. - Nicola Riolini',
    'website': 'http://www.micronaet.it',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'product',
        ],
    'data': [
        'security/stats_group.xml',
        'security/ir.model.access.csv',
        'views/stats_view.xml',
        #'data/color_data.xml',
        ],
    'external_dependencies': {
        'python': ['xlsxwriter'],
        },
    'application': False,
    'installable': True,
    'auto_install': False,
    }
