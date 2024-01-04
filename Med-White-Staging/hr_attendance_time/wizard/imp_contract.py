# -*- coding: utf-8 -*-

import xlrd
import base64
from datetime import datetime
import logging
from dateutil import parser

from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.addons.base.models.res_partner import _tz_get
# from odoo.addons.resource.models.resource import make_aware
from odoo.addons.hr_attendance_time.models.attendance import to_naive_utc

_logger = logging.getLogger(__name__)
IGNORE_WORDS = ['', ' ', '-']

START_ROW_AT = 1
STOP_ROW_AT = START_ROW_AT + 20000


class ImportEmployeeAttendance(models.TransientModel):
    _name = 'import.employee.contract'
    _description = 'Import Employee contract'

    file = fields.Binary('File', required=True)
    name = fields.Char('File Name')
    tz = fields.Selection(
        _tz_get, string='Timezone', required=True,
        default=lambda self: self._context.get('tz') or self.env.user.tz or 'UTC',
        help="This field is used in order to define in which timezone the resources will work.")
    # start_at = fields.Integer("Start At", default=0)
    # stop_at = fields.Integer("Stop At", default=20000)

    def parse_file(self, sheet):
        file_data = []
        ignored_lines = []
        skipped_lines = []

        def shouldIgnore(s):
            if not s or s in IGNORE_WORDS:
                return True
            return False

        def xl_dtime(value):
            if not value:
                return False
            if type(value) == float:
                return datetime(*xlrd.xldate.xldate_as_tuple(value, sheet.book.datemode))
            elif type(value) == str:
                return parser.parse(value)
            return ''

        # [
        #     '9002 cont1', 9002.0, 'Mohamed Abdul Kader  Mohamed Ibrahim', 'Purchase Manager',
        #     'Shift 1 ( 8:30 AM : 17:00 PM )', 42198.0, '', 'Running', 'Grey',
        #     'Boutiqaat Holding', 1.0,
        #     '', 25.0, '', '', '',
        #     100.0, '', 15.0, '', '',
        #     10.0, '', '', '', '',
        #     0.4, 60.0, '', 43817.0, 216451153.0,
        #     '288022502752'
        # ]

        header_names = [
            'name', 'emp_code', 'emp_name', 'job_name',
            'resource_calendar_id', 'date_start', 'date_end', 'state', 'kanban_state',
            'company_id', 'active',
            'advantages', 'books_allowance', 'commission', 'driver_fuel_allowance', 'trial_date_end',
            'wage', 'hourly_wage', 'housing_allowance', 'hr_responsible_id', 'meal_allowance',
            'mobile_allowance', 'motor_vehicle_allowance', 'night_shift_allowance', 'pf_allowance', 'special_other_allowance',
            'staff_discount', 'staff_max_discount', 'transport_allowance', 'visa_expire', 'visa_no',
            'permit_no'
        ]

        for r in range(START_ROW_AT or 1, min(STOP_ROW_AT, sheet.nrows)):
            row = sheet.row_values(r)
            print ('___ row : ', row)

            # Check IN Time Must be present
            if shouldIgnore(row[0]) or shouldIgnore(row[2]) or not any(row[:4]):
                _logger.info("____ IGNORE : %s %s %s", row[0], row[1], any(row[:4]))
                ignored_lines.append(','.join(map(str, row)))
                continue

            try:

                record = dict(zip(header_names, row))
                # from pprint import pprint
                # print('__________ record : ')
                # pprint(record)
                emp_code = record['emp_code'] = str(int(record['emp_code']))
                record['date_start'] = xl_dtime(record['date_start'])
                record['date_end'] = xl_dtime(record['date_end'])
                record['trial_date_end'] = xl_dtime(record['trial_date_end'])
                record['visa_expire'] = xl_dtime(record['visa_expire'])

                # check_out = False
                # if row[3]:
                #     check_out = xl_dtime(row[3])
                #     if check_out < check_in:
                #         s = '%s :: %s :: Check Out Time `%s` Less then Check In Time `%s`' % (r, emp_code, check_out, check_in)
                #         _logger.info("____ %s ", s)
                #         skipped_lines.append(s)
                #         continue

                _logger.info("____ Adding : %s :: %s %s", r, emp_code, record['emp_name'])
                file_data.append({
                    'row_index': r,
                    'record': record,
                    'emp_code': emp_code
                })
            except Exception as e:
                line = ','.join(map(str, row[:4]))
                raise UserError(_('Please Check Row #%s\nLine : %s\nProblem : %s') % (r, line, e))
        _logger.info("____ Total Records : %s", len(file_data))
        _logger.info("____ Total Ignored : %s", len(ignored_lines))
        _logger.info("____ Total Skipped : %s", len(skipped_lines))
        return file_data, ignored_lines, skipped_lines

    def import_contract(self):
        self.ensure_one()
        contracts = Contract = self.env['hr.contract']
        cr = self.env.cr

        def get_id(table, where, params=()):
            sql = """
            SELECT id FROM """ + table + """ WHERE """ + where + """ LIMIT 1
            """
            cr.execute(sql, params)
            res = cr.fetchone()
            return res and res[0] or False

        wb = xlrd.open_workbook(file_contents=base64.decodestring(self.file))

        sheet = wb.sheets()[0]
        records, ignored_lines, skipped_lines = self.parse_file(sheet)
        emp_not_found = []
        _logger.info("____ Skipped Lines : %s", ignored_lines)

        shifts = {
            'Shift 1': 10, 'Shift 2': 17,
            'Shift 3': 12, 'Shift 4': 13,
            'Shift 7': 16, 'Shift 8': 18,
            'Shift 9': 19,
            'Exception': 21,
        }

        shifts.update({'Shift 5': 14, 'Shift 6': 15})

        for line in sorted(records, key=lambda a: (a['row_index'])):
            print ('___ line : ', line)

            emp_id = get_id("hr_employee", "identification_id = %s", (line['emp_code'],))
            # sql = """
            # SELECT id FROM hr_employee WHERE identification_id = %s LIMIT 1
            # """
            # cr.execute(sql, (line['emp_code'],))
            # res = cr.fetchone()
            if emp_id:
                vals = line['record']
                resource_calendar_id = shifts.get(vals['resource_calendar_id']) or 10
                # pprint(line["record"])
                vals.pop('emp_code')
                vals.pop('emp_name')
                vals.pop('state')
                vals.pop('kanban_state')
                vals.pop('job_name')
                vals.update({
                    'employee_id': emp_id,
                    'resource_calendar_id': resource_calendar_id,
                    'company_id': 1
                })
                contracts += Contract.sudo().create(vals)
            else:
                emp_not_found.append(', '.join(map(str, line.values())))
                _logger.info("____ Employee Not Found : Row = %s, Code = %s", line['row_index'], att['emp_code'])
        if contracts:

            log = self.env['att.upload.log'].create({
                'name': "Contract : " + self.name,
                'file': self.file,
                # 'contract_ids': [(4, _id) for _id in attendances.ids],
                'skipped_count': len(skipped_lines),
                'skipped_text': '\n'.join(skipped_lines),
                'ignored_count': len(ignored_lines),
                'ignored_text': '\n'.join(ignored_lines),
                'no_emp_count': len(emp_not_found),
                'no_emp_text': '\n'.join(emp_not_found),
            })
            # sql = """
            # UPDATE hr_attendance SET att_log_id = %s WHERE id IN %s
            # """
            # cr.execute(sql, (log.id, tuple(attendances.ids),))
            action = self.env.ref('hr_attendance_time.att_upload_log_action').read()[0]
            action.update({
                'res_id': log.id,
                'view_mode': 'form',
                'domain': [('id', '=', log.id)]
            })
            return action
