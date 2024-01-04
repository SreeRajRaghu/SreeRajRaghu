# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import pymssql

import logging


_logger = logging.getLogger(__name__)


class MssqlConfig(models.Model):
    _name = 'mssql.config'
    _description = 'MSSQL Configuration'

    # driver = fields.Char(string='Driver', required=True)
    host = fields.Char(string='Host', required=True)
    # port = fields.Char(string='Port', required=True)
    username = fields.Char(string='Username', required=True)
    password = fields.Char(string='Password', required=True)
    database = fields.Char(string='Database Name', required=True)
    last_inserted = fields.Datetime(string='Last Inserted')
    last_read = fields.Datetime(string='Last Read')
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection([('draft', 'Not Connected'), ('connected', 'Connected')], default='draft')
    scheduler_ids = fields.One2many(comodel_name="medical.config", inverse_name="scheduler_id", string="scheduler", required=False, )

    def get_connection(self):
        # self.ensure_one()
        if not self:
            return
        server = self.host
        database = self.database
        username = self.username
        password = self.password
        try:
            conn = pymssql.connect(server=server, user=username, password=password, database=database)
        except Exception as e:
            self.state = 'draft'
            raise UserError(_('Not able to connect to the database. Please check your credentials.'))
        self.state = 'connected'
        return conn

    def _get_connection(self):
        # config = self.search([], limit=1)
        config = self
        return config.get_connection()

    def check_for_update(self,limit_val=False, lab_test_names=False,selected_results= False):
        for rec in self:
            conn = rec._get_connection()
            if not conn:
                return
            cursor = conn.cursor()
            MedicalLabTest = self.env['medical.lab.test']
            MedicalLabResultcriteria = self.env['medical.lab.resultcriteria']
            # if lab_test_names:
            #     lab_tests = MedicalLabTest.search([('state', '=', 'inprogress'), ('name', 'in', lab_test_names)])
            # else:
            if selected_results:
                lab_tests = MedicalLabTest.search([('state', '=', 'inprogress'),('id','in',selected_results)])
            else:
                lab_tests = MedicalLabTest.search([('state', '=', 'inprogress')])
            lab_test_names = lab_tests.mapped('name')
            case_names = []
            for test in lab_tests:
                for line in test.lab_test_criteria_ids.filtered(lambda a: (not a.result and a.name) and not a.result_fetched):
                    case_names.append(line.name)

            if lab_test_names:
                lab_test_names = '(' + ', '.join(["'"+test_name+"'" for test_name in lab_test_names]) + ')'
                case_names = '(' + ', '.join(["'"+test_name+"'" for test_name in case_names]) + ')'
                limit_clause = ''
                if limit_val:
                    limit_clause = ' ORDER BY SampleNo OFFSET 0 ROWS FETCH NEXT ' + str(limit_val) + ' ROWS ONLY'
                query = "SELECT SampleNo, LIMSTestParam, ResultValue  from Analyzer_ResultDetail where LIMSTestParam in " + case_names + " AND SampleNo in " + lab_test_names + limit_clause
                logging.info("___ Trying to Fetch : %s" % (query))
                cursor.execute(query)
                rows = cursor.fetchall()
                columns = [column[0] for column in cursor.description]
                logging.info("___ Fetched Rows: %s - %s - %s", columns, len(rows or []))
                for row in rows:
                    data_dict = dict(zip(columns, row))
                    if data_dict['LIMSTestParam']:
                        domain = [
                            ('medical_lab_test_id.name', '=', data_dict['SampleNo']),
                            ('case_id.name', '=', data_dict['LIMSTestParam']),
                            ('result', '=', False),
                        ]
                        lab_test_criteria = MedicalLabResultcriteria.search(domain, limit=1)
                        logging.info("___ Lab Result : %s - %s", lab_test_criteria, data_dict)
                        if lab_test_criteria:
                            lab_test_criteria.write({'result': data_dict['ResultValue'],'result_fetched':True})
                if rows:
                    vals = {
                        'name': 'Read',
                        'description': '',
                        'request': query,
                        'response': rows,
                    }
                    self.env['mssql.log'].create(vals)

    def execute_query(self, query):
        conn = self._get_connection()
        if not conn:
            return
        cursor = conn.cursor()
        try:
            cursor.execute(query)
            conn.commit()
        except Exception as e:
            _logger.error(e)
        finally:
            conn.close()
            if query:
                self.env['mssql.log'].create({'name': 'Write', 'description': '', 'request': query})


class MssqlLog(models.Model):
    _name = 'mssql.log'
    _description = 'MSSQL Log'

    name = fields.Char(string='Action', required=True)
    description = fields.Char(string='Description')
    request = fields.Char(string='Request')
    response = fields.Char(string='Response')


class LabTests(models.Model):
    _inherit = 'medical.lab.test'

    def set_to_test_inprogress(self):
        res = super(LabTests, self).set_to_test_inprogress()
        for rec in self:
            vals = []
            first_name = last_name = ''
            full_name = rec.partner_id.name and rec.partner_id.name[:20] or rec.partner_id.phone or ''
            if ' ' in full_name:
                full_name = full_name.strip()
                full_name = full_name.split(' ')[:2]
                first_name = full_name[0][:10]
                last_name = full_name[-1][:10]
            dt = (rec.date_analysis or fields.Datetime.now()).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            # rec.partner_id.name, rec.partner_id.name
            for test_id in rec.lab_test_criteria_ids:
                if test_id.case_id:
                    vals.append(
                        """('%s', '%s', '%s', '%s', '%s', '%s')""" % (
                            rec.name, test_id.case_id.name, dt, first_name, last_name, str(rec.partner_id.id)))
            if vals:
                vals = ', '.join(vals)
                query = """INSERT INTO Analyzer_Order (SampleNo, LIMSTestParam, OrderDateTime, PatFirstName, PatLastName, PatientID) VALUES %s""" % (
                    vals)
                # self.env['mssql.config'].execute_query(query)
                mssql_obj = self.env['mssql.config'].search([('scheduler_ids','in',rec.appointment_id.config_id.id)], limit=1)
                mssql_obj.execute_query(query)
        return res

    def update_sql_data(self):
        for rec in self:
            medical_lab_test_records = rec.ids

            # for lab_rec in medical_lab_test_records:
            scheduler = rec.appointment_id.config_id.id
            mssql_obj = self.env['mssql.config'].search([('scheduler_ids', 'in', scheduler)],limit=1)
            mssql_obj.check_for_update(selected_results=medical_lab_test_records)



