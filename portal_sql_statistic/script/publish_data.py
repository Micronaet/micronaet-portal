#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2020  Micronaet SRL (<http://www.micronaet.it>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# Script for Python 2.7

import os
import sys
import pickle

DEFAULT_SERVER_DATE_FORMAT = "%Y-%m-%d"


class PortalAgent:
    """ Agent for access to SQL Server
    """
    def __init__(self, config_file, mode):
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
        available_years = range(from_year, current_year + 1)
        for year in available_years:
            if year == current_year:
                text_year = ''
            elif year_format == 'yy':  # 2 char
                text_year = '%02d' % (year - 2000)
            else:
                text_year = year

            database_list[year] = '%s%s' % (
                database, text_year)

        # Read parameters:
        self.parameters = {
            'mode': mode,
            'mysql': {
                'hostname': '%s' % (  # :%s' % (
                    config.get('mysql', 'server'),
                    # config.get('mysql', 'port'),
                    ),

                'username': config.get('mysql', 'username'),
                'password': config.get('mysql', 'password'),

                'database': database_list,
                'table': {
                    'header': 'MM_TESTATE' if uppercase else 'mm_testate',
                    'line': 'MM_RIGHE' if uppercase else 'mm_righe',
                    },
                'agent_file': config.get('mysql', 'agent_file'),
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

                'origin_folder': os.path.expanduser(
                    config.get('transfer', 'origin_folder')),
                'remote_folder': os.path.expanduser(
                    config.get('transfer', 'remote_folder')),
                },

            'pickle_file': {
                'partner': 'partner.pickle',
                'product': 'product.pickle',
                'reason': 'reason.pickle',
                'currency': 'currency.pickle',
                'sector': 'sector.pickle',
                'statistic': 'statistic.pickle',
                },
            }

        # Create Years list in model:
        """
        TODO Run only when remote!
        year_pool = self._get_odoo_model('pivot.year')
        for year in available_years:
            if not year_pool.search([('name', '=', year)]):
                year_pool.create({
                    'name': year,
                    'filename': '%s.pickle',
                    'load': True,
                })
                """

    def _get_odoo(self):
        """ Return ODOO Erpeek connection
        """
        import erppeek

        return erppeek.Client(
            self.parameters['odoo']['url'],
            db=self.parameters['odoo']['database'],
            user=self.parameters['odoo']['username'],
            password=self.parameters['odoo']['password'])

    def _get_odoo_model(self, model_name):
        """ Return ODOO Erpeek connection
        """
        odoo = self._get_odoo()
        return odoo.model(model_name)

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

    def _extract_key(self, record):
        """ Get key for header and line table
        """
        return (
            record['CSG_DOC'],
            record['NGB_SR_DOC'],
            record['NGL_DOC'],
            )

    def _import_generic_model(
            self, records, model, key_field, name, verbose=100):
        """ Procedure for import similar model records
        """
        def load_extra_pool(model):
            """ Load extra pool for particular model
            """
            extra_pool = {}
            if model == 'res.partner':
                # Load country:
                country_pool = self._get_odoo_model('res.country')
                extra_pool['country'] = {}
                country_ids = country_pool.search([])
                for country in country_pool.browse(country_ids):
                    extra_pool['country'][country.code] = country.id

                # Load partner (agent, salesman, supervisor):
                partner_pool = self._get_odoo_model('res.partner')
                extra_pool['partner'] = {}
                partner_ids = partner_pool.search([])
                for partner in partner_pool.browse(partner_ids):
                    extra_pool['partner'][partner.ref] = partner.id

            if model in ('product.template', 'pivot.product.statistic'):
                # Load sector:
                sector_pool = self._get_odoo_model('pivot.product.sector')
                extra_pool['sector'] = {}
                sector_ids = sector_pool.search([])
                for sector in sector_pool.browse(sector_ids):
                    extra_pool['sector'][sector.account_ref] = sector.id

            if model == 'product.template':
                # Load statistic:
                statistic_pool = self._get_odoo_model(
                    'pivot.product.statistic')
                extra_pool['statistic'] = {}
                statistic_ids = statistic_pool.search([])
                for statistic in statistic_pool.browse(statistic_ids):
                    extra_pool['statistic'][statistic.account_ref] = \
                        statistic.id
            return extra_pool

        def integrate_foreign_keys(model, record, extra_pool):
            """ Integrate extra foreign keys updating record
            """
            if model == 'res.partner':
                record['country_id'] = extra_pool['country'].get(
                    record['country_code'])
                del(record['country_code'])

                record['salesman_id'] = extra_pool['partner'].get(
                    record['salesman_code'])
                del(record['salesman_code'])

                record['responsible_id'] = extra_pool['partner'].get(
                    record['responsible_code'])
                del(record['responsible_code'])

                record['agent_id'] = extra_pool['partner'].get(
                    record['agent_code'])
                del(record['agent_code'])

                responsible_id
            if model in ('pivot.product.statistic', 'product.template'):
                record['sector_id'] = extra_pool['sector'].get(
                    record['sector_code'])
                del(record['sector_code'])

            if model == 'product.template':
                record['statistic_id'] = extra_pool['statistic'].get(
                    record['statistic_code'])
                del(record['statistic_code'])

        res = {}
        model_pool = self._get_odoo_model(model)
        total = len(records)
        print('Load %s mode: %s' % (name, self.parameters['mode']))

        if self.parameters['mode'] == 'load':
            record_ids = model_pool.search([])
            for record in model_pool.browse(record_ids):
                res[eval('record.%s' % key_field)] = record.id
            return res

        # ---------------------------------------------------------------------
        # Update / Write mode:
        # ---------------------------------------------------------------------
        # Load extra pool for foreign keys resolution:
        extra_pool = load_extra_pool(model)

        i = 0
        for record in records:
            i += 1
            if not i % verbose:
                print('%s / %s %s updated' % (i, total, name))
            key = record[key_field]
            model_ids = model_pool.search([
                (key_field, '=', key),
                ])

            # Integrate record with foreign keys:
            integrate_foreign_keys(model, record, extra_pool)
            if model_ids:
                if self.parameters['mode'] == 'update':
                    model_pool.write(model_ids, record)
                model_id = model_ids[0]
            else:
                model_id = model_pool.create(record).id

            res[key] = model_id
        return res

    def extract_data(self, last=False):
        """ Extract all data in output folder
        """
        import pickle
        export_path = self.parameters['transfer']['origin_folder']
        extra_file = self.parameters['pickle_file']

        # Preload:
        agent_file = self.parameters['mysql']['agent_file']
        agent_db = {}
        print('Read extra file for agent: %s' % agent_file)
        for line in open(agent_file, 'r'):
            line = line.strip()
            row = line.split('|')
            agent_db[row[0].strip()] = (  # Customer code
                row[2].strip(),  # Salesman
                row[4].strip(),  # Supervisor
                row[6].strip(),  # Agent
                )

        # TODO parameter:
        supplier_code = '2'
        customer_code = '4'
        start_code_used = supplier_code + customer_code

        query_header = "SELECT * FROM %s;" % (
            self.parameters['mysql']['table']['header'])

        query_line = "SELECT * FROM %s;" % (
            self.parameters['mysql']['table']['line'])

        year_list = sorted(self.parameters['mysql']['database'])
        if last:
            year_list = year_list[-1:]

        for year in year_list:
            database = self.parameters['mysql']['database'][year]
            cr = self._sql_connect(database)
            odoo_data = []
            header_db = {}
            tot = {
                'header': 0,
                'line': 0,
                }

            if year_list[-1] == year:
                # -------------------------------------------------------------
                # Last year operation:
                # -------------------------------------------------------------
                print('Start last connection operations:')

                # Export partner:
                cr.execute('SELECT * FROM PA_RUBR_PDC_CLFR;')
                partner_data = []
                for partner in cr.fetchall():
                    account_ref = partner['CKY_CNT'].strip()
                    account_ref_1 = account_ref[:1]
                    if account_ref_1 not in start_code_used:
                        continue

                    agent_data = agent_db.get(account_ref, ('', '', ''))
                    partner_data.append({
                        'pivot_partner': True,
                        'is_company': True,
                        'customer': account_ref_1 == supplier_code,
                        'supplier': account_ref_1 == customer_code,
                        'account_ref': account_ref,
                        'name': partner['CDS_CNT'].strip(),
                        'country_code': partner['CKY_PAESE'].strip().upper(),
                        'account_mode': partner['IST_NAZ'].strip(),

                        # Agent part:
                        'salesman_code': agent_data[0],
                        'responsible_code': agent_data[1],
                        'agent_code': agent_data[2],
                        })
                pickle.dump(
                    partner_data, open(
                        os.path.join(export_path, extra_file['partner']),
                        'wb'))
                print('Export partner [# %s]' % len(partner_data))

                # Export product
                cr.execute('SELECT * FROM AR_ANAGRAFICHE;')
                product_data = []
                for product in cr.fetchall():
                    stat_key = '%s%02d' % (
                        product['CKY_CAT_STAT_ART'],
                        product['NKY_CAT_STAT_ART'],
                        )
                    product_data.append({
                        'pivot_product': True,
                        'default_code': product['CKY_ART'].strip(),
                        'name': '%s%s' % (
                            product['CDS_ART'].strip(),
                            product['CSG_ART_ALT'].strip(),
                            ),
                        'sector_code': product['CKY_CAT_STAT_ART'],
                        'statistic_code': stat_key,
                        })
                pickle.dump(
                    product_data, open(
                        os.path.join(export_path, extra_file['product']),
                        'wb'))
                print('Export product [# %s]' % len(product_data))

                # Export reason movement
                cr.execute('SELECT * FROM MC_CAUS_MOVIMENTI;')
                reason_data = []
                for reason in cr.fetchall():
                    reason_data.append({
                        'account_ref': str(reason['NKY_CAUM']),
                        'name': reason['CDS_CAUM'].strip(),
                        })
                pickle.dump(
                    reason_data, open(
                        os.path.join(export_path, extra_file['reason']),
                        'wb'))
                print('Export reason [# %s]' % len(reason_data))

                # Export currency
                cr.execute('''SELECT * FROM MU_VALUTE WHERE CDS_VLT!='';''')
                currency_data = []
                for currency in cr.fetchall():
                    currency_data.append({
                        'account_ref': str(currency['NKY_VLT']),
                        'name': currency['CDS_VLT'].strip(),
                        'symbol': currency['CSG_VLT'].strip(),
                        })
                pickle.dump(
                    currency_data, open(
                        os.path.join(export_path, extra_file['currency']),
                        'wb'))
                print('Export currency [# %s]' % len(currency_data))

                # Export sector and statistic category:
                cr.execute('SELECT * FROM MY_CAT_STAT_ART;')
                sector_done = []
                sector_data = []
                statistic_data = []
                for statistic in cr.fetchall():
                    # Sector part:
                    key = statistic['CKY_CAT_STAT_ART'].strip()
                    if key not in sector_done:
                        sector_data.append({
                            'account_ref': key,
                            'name': key,
                            })
                        sector_done.append(key)

                    # Statistic part:
                    stat_key = '%s%02d' % (key, statistic['NKY_CAT_STAT_ART'])
                    statistic_data.append({
                        'sector_code': key,
                        'account_ref': stat_key,
                        'name': statistic['CDS_CAT_STAT_ART'].strip(),
                        })

                pickle.dump(
                    sector_data, open(
                        os.path.join(export_path, extra_file['sector']),
                        'wb'))
                print('Export sector [# %s]' % len(sector_data))

                pickle.dump(
                    statistic_data, open(
                        os.path.join(export_path, extra_file['statistic']),
                        'wb'))
                print('Export statistic [# %s]' % len(statistic_data))

            # -----------------------------------------------------------------
            # Load header:
            # -----------------------------------------------------------------
            cr.execute(query_header)
            for record in cr.fetchall():
                tot['header'] += 1

                key = self._extract_key(record)
                if key not in header_db:
                    header_db[key] = record

            # -----------------------------------------------------------------
            # Load line
            # -----------------------------------------------------------------
            cr.execute(query_line)
            for record in cr.fetchall():
                tot['line'] += 1

                key = self._extract_key(record)
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

                # Sign is for sales not for stock
                if key[0] in ('BC', 'SL', 'BS'):  # not used BD
                    sign = +1
                else:  # BF, RC, CL
                    sign = -1

                qty = record['NQT_RIGA_ART_PLOR']
                qty_rate = 1  # TODO no more used? record['NCF_CONV'] or 1
                qty *= sign / qty_rate
                # TODO Causale di vendita

                exchange = header['NCB_VLT_ESTER_EURO'] or 1.0
                subtotal = price * qty
                odoo_data.append({
                    'year': year,
                    'name': ref,

                    'date': date,
                    'document_type': key[0],  # BC BD SL CL BF BS RC
                    'mode': 'sale',  # sale transport discount fee

                    'partner_code': header['CKY_CNT_CLFR'],
                    'product_code': record['CKY_ART'],
                    'reason_code': header['NKY_CAUM'],
                    'currency_code': header['NKY_VLT'],

                    'product_uom_qty': qty,
                    'list_price': price,
                    'exchange': exchange,
                    'subtotal': subtotal / exchange,
                    'currency_subtotal': subtotal,
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
        path = self.parameters['transfer']['remote_folder']
        extra_file = self.parameters['pickle_file']

        # ---------------------------------------------------------------------
        # Pre operations (extra model data):
        # ---------------------------------------------------------------------
        # No need to import sector_id and statistic_id
        fullname = os.path.join(path, extra_file['sector'])
        self._import_generic_model(
            pickle.load(open(fullname, 'rb')),
            'pivot.product.sector', 'account_ref', 'sector')

        fullname = os.path.join(path, extra_file['statistic'])
        self._import_generic_model(
            pickle.load(open(fullname, 'rb')),
            'pivot.product.statistic', 'account_ref', 'statistic')

        fullname = os.path.join(path, extra_file['currency'])
        currency_db = self._import_generic_model(
            pickle.load(open(fullname, 'rb')),
            'pivot.currency', 'account_ref', 'currency')

        fullname = os.path.join(path, extra_file['reason'])
        reason_db = self._import_generic_model(
            pickle.load(open(fullname, 'rb')),
            'pivot.sale.reason', 'account_ref', 'sale reason')

        fullname = os.path.join(path, extra_file['product'])
        product_db = self._import_generic_model(
            pickle.load(open(fullname, 'rb')),
            'product.template', 'default_code', 'product')

        fullname = os.path.join(path, extra_file['partner'])
        partner_db = self._import_generic_model(
            pickle.load(open(fullname, 'rb')),
            'res.partner', 'account_ref', 'partner')

        # ---------------------------------------------------------------------
        # File to be imported:
        # ---------------------------------------------------------------------
        stats_pool = self._get_odoo_model('pivot.sale.line')

        file_list = []
        for root, folders, files in os.walk(path):
            for filename in files:
                if filename in extra_file.values():
                    print('Jump no stats file: %s...' % filename)
                    continue
                file_list.append(filename)
            break
        file_list = sorted(file_list)  # File list

        if last:
            file_list = file_list[-1:]
        for filename in file_list:
            fullname = os.path.join(path, filename)
            print('Importing %s file...' % fullname)

            # Delete all line record for this year
            year = int(filename.split('.')[0])
            stats_ids = stats_pool.search([
                ('year', '=', year)])

            if stats_ids:
                print('Remove %s record for year: %s' % (
                    len(stats_ids), year))
                stats_pool.unlink(stats_ids)

            # Reload all pickle file for this year
            i = 0
            for record in pickle.load(open(fullname, 'rb')):
                i += 1
                if not i % 20:
                    print('Import year %s [%s]' % (year, i))

                # -------------------------------------------------------------
                # Integration:
                # -------------------------------------------------------------
                record['partner_id'] = partner_db.get(
                    record['partner_code'])
                del(record['partner_code'])

                record['product_id'] = product_db.get(
                    record['product_code'])
                del(record['product_code'])

                record['reason_id'] = reason_db.get(
                    record['reason_code'])
                del(record['reason_code'])

                record['currency_id'] = currency_db.get(
                    record['currency_code'])
                del(record['currency_code'])

                stats_pool.create(record)


if __name__ != '__main__':
    print('Procedure is not callable externally!')

# Check parameter (for send or receive mode startup):
mode_list = [
    'create',  # Only create new
    'update',  # Create and update
    'load',  # Load only (no file will be read)
    ]
update_mode = 'load'

argv = sys.argv
if len(argv) < 2:
    print('Pass the parameter: publish, publish_last, import, import_last')
    sys.exit()
else:
    parameter = argv[1]

if len(argv) == 3:
    if argv[2] in mode_list:
        update_mode = argv[2]
    else:
        print('Mode parameter not in %s list' % (mode_list, ))
        sys.exit()
print('Launch as %s, update mode: %s' % (parameter, update_mode))

portal_agent = PortalAgent('./openerp.cfg', update_mode)

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
