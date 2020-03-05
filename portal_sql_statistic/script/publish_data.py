#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2020  Micronaet SRL (<http://www.micronaet.it>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# Script for Python 2.7

import os
import sys

DEFAULT_SERVER_DATE_FORMAT = "%Y-%m-%d"


class PortalAgent:
    """ Agent for access to SQL Server
    """
    def __init__(self, config_file):
        """ Access to MySQL server with parameter in Config file
        """
        import ConfigParser
        from datetime import datetime

        # Read config file:
        cfg_file = os.path.expanduser(config_file)
        config = ConfigParser.ConfigParser()
        config.read([cfg_file])

        # ---------------------------------------------------------------------
        # Generate database name:
        # ---------------------------------------------------------------------
        database = config.get('mysql', 'database')
        from_year = int(config.get('mysql', 'year_from'))
        year_format = config.get('mysql', 'year_format')
        uppercase = config.get('mysql', 'uppercase')
        current_year = int(datetime.now().year)

        database_list = {}
        for year in range(from_year, current_year + 1):
            if year == current_year:
                text_year = ''
            elif year_format == 'yy': # 2 char
                    text_year = '%02d' % (year - 2000)
            else:
                text_year = year

            database_list[year] = '%s%s' % (
                database, text_year)

        # Read parameters:
        self.parameters = {
            'mysql': {
                'hostname': '%s' % (#:%s' % (
                    config.get('mysql', 'server'),
                    #config.get('mysql', 'port'),
                    ),

                'username': config.get('mysql', 'username'),
                'password': config.get('mysql', 'password'),

                'database': database_list,
                'table': {
                    'header': 'MM_TESTATE' if uppercase else 'mm_testate',
                    'line': 'MM_RIGHE' if uppercase else 'mm_righe',
                    },
                },

            'odoo': {
                'url': r'http://%s:%s' % (
                    config.get('odoo', 'server'),
                    config.get('odoo', 'port'),
                    ),
                'database': config.get('odoo', 'database'),
                'username': config.get('odoo', 'username'),
                'password': config.get('odoo', 'password'),
                },

            'transfer': {
                'server': config.get('transfer', 'server'),
                'port': config.get('transfer', 'port'),
                'username': config.get('transfer', 'username'),
                'password': config.get('transfer', 'password'),

                'origin_folder': config.get('transfer', 'origin_folder'),
                'remote_folder': config.get('transfer', 'remote_folder'),
                },
            }

    def _get_odoo(self):
        """ Return ODOO Erpeek connection
        """
        import erppeek

        return erppeek.Client(
            self.parameters['odoo']['url'],
            db=self.parameters['odoo']['database'],
            user=self.parameters['odoo']['username'],
            password=self.parameters['odoo']['password'],
            )

    def _get_odoo_model(self, model_name):
        """ Return ODOO Erpeek connection
        """
        odoo = self._get_odoo()

        return odoo.model(model_name)

        return odoo
    def _sql_connect(self, database):
        """ Connect to MySQL server
        """
        try:
             import MySQLdb, MySQLdb.cursors
        except:
            print('Error no module MySQLdb installed!')
            return False

        connection = MySQLdb.connect(
            host=self.parameters['mysql']['hostname'],
            user=self.parameters['mysql']['username'],
            passwd=self.parameters['mysql']['password'],
            db=database,
            cursorclass=MySQLdb.cursors.DictCursor,
            charset='utf8',
            )

        cursor = connection.cursor()
        if not cursor:
            print('Can\'t access in MSSQL Database: %s!' % database)
            return False
        return cursor

    def _get_key(self, record):
        """ Get key for header and line table
        """
        return (
            record['CSG_DOC'],
            record['NGB_SR_DOC'],
            record['NGL_DOC'],
        )

    def extract_data(self, last=True):
        """ Extract all data in output folder
        """
        import pickle

        export_path = self.parameters['transfer']['origin_folder']

        query_header = """
            SELECT *
            FROM %s;
            """ % self.parameters['mysql']['table']['header']

        query_line = """
            SELECT *
            FROM %s;
            """ % self.parameters['mysql']['table']['line']

        year_list = sorted(self.parameters['mysql']['database'])
        if last:
            year_list = year_list[-1:]

        for year in year_list:
            database = self.parameters['mysql']['database'][year]
            odoo_data = []
            header_db = {}
            tot = {
                'header': 0,
                'line': 0,
                }
            cr = self._sql_connect(database)

            # -----------------------------------------------------------------
            # Load header:
            # -----------------------------------------------------------------
            cr.execute(query_header)
            for record in cr.fetchall():
                tot['header'] += 1

                key = self._get_key(record)
                if key not in header_db:
                    header_db[key] = record

            # -----------------------------------------------------------------
            # Load line
            # -----------------------------------------------------------------
            cr.execute(query_line)
            for record in cr.fetchall():
                tot['line'] += 1

                key = self._get_key(record)
                if key not in header_db:
                    print('Header line not present: %s' % (key, ))
                header = header_db[key]

                # -------------------------------------------------------------
                # Generate record list for ODOO:
                # -------------------------------------------------------------
                ref = '%s %s/%s' % key
                date = header['DTT_DOC'].strftime(DEFAULT_SERVER_DATE_FORMAT)
                price = record['NPZ_UNIT']

                if key[0] == 'BD':
                    continue  # Not used for now

                if key[0] in ('BC', 'SL', 'BS'): # not used BD
                    sign = -1
                else:  # BF, RC, CL
                    sign = +1

                qty = record['NQT_RIGA_ART_PLOR']
                qty_rate = record['NCF_CONV'] or 1
                qty *= sign / qty_rate
                # TODO Causale di vendita

                odoo_data.append({
                    'year': year,
                    'name': ref,

                    'date': date,
                    'document_type': key[0],  # BC BD SL CL BF BS RC
                    'mode': 'sale',  # sale transport discount fee

                    # 'partner_id'
                    # 'country_id'
                    # 'agent_id'
                    # 'salesman_id'
                    # 'responsible_id'

                    # 'product_id'
                    # 'uom_id'
                    # 'category_id'

                    'product_uom_qty': qty,
                    'list_price': price,
                    'subtotal': price * qty,
                })

            # -----------------------------------------------------------------
            # Write pickle file:
            # -----------------------------------------------------------------
            pickle_filename = os.path.join(export_path, '%s.pickle' % year)
            pickle.dump(odoo_data, open(pickle_filename, 'wb'))
            print('Exported header: %s, line: %s on file: %s >> record %s' % (
                pickle_filename,
                tot['header'],
                tot['line'],
                len(odoo_data),
                ))
        return True

    def publish_data(self):
        """ Rsync items to remote server
        """
        command = 'rsync -avh -e "ssh -p %s" %s/* %s@%s:%s' % (
            self.parameters['transfer']['port'],

            self.parameters['transfer']['origin_folder'],

            self.parameters['transfer']['username'],
            self.parameters['transfer']['server'],
            self.parameters['transfer']['remote_folder'],
            # 'password': config.get('transfer', 'password'),
            )
        print('Transfer via rsync: %s' % command)
        os.system(command)

    def import_data(self, last=False):
        """ Import data on Remote ODOO
        """
        stats_pool = self._get_odoo_model('pivot.sale.line')

        # ---------------------------------------------------------------------
        # File to be imported:
        # ---------------------------------------------------------------------
        path = self.parameters['transfer']['remote_folder']
        import pdb; pdb.set_trace()

        for root, folders, files in os.walk(path):
            file_list = sorted(files)  # File list
            break

        if last:
            file_list = file_list[-1:]

        for filename in file_list:
            print('Importing %s file...' % filename)

            # Delete all line record for this year
            year = int(filename.split('.')[0])
            stats_line = stats_pool.search([
                ('year', '=', year)])
            stats_line.unlink()

            # Reload all pickle file for this year
            for record in pickle.load(open(filename, 'rb')):
                stats_pool.create(record)


if __name__ != '__main__':
    print('Procedure is not callable externally!')

# Check parameter (for send or receive mode startup):
argv = sys.argv
if len(argv) == 2:
    parameter = argv[1]
else:
    print('Pass the parameter: publish, publish_last, import, import_last')
    sys.exit()

portal_agent = PortalAgent('./openerp.cfg')
if parameter in 'publish':
    portal_agent.extract_data()
    portal_agent.publish_data()
elif parameter in 'publish_last':
    portal_agent.extract_data(last=True)
    portal_agent.publish_data()
elif parameter == 'import':
    portal_agent.import_data()
elif parameter == 'import_last':
    portal_agent.import_data(last=True)
else:
    print('Missed parameter: publish or import')
    sys.exit()

"""
        if default_code[:1] in 'AB':
            product_type = 'Materie prime'
        elif default_code[:1] in 'M':
            product_type = 'Macchinari'
        else:   
            product_type = 'Prodotti finiti'
   """
