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
    _name = 'import.employee.attendance'
    _description = 'Import Employee attendance'

    file = fields.Binary('File')
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

        file_tz = self.tz

        def xl_dtime(value):
            if type(value) == float:
                return datetime(*xlrd.xldate.xldate_as_tuple(value, sheet.book.datemode))
            elif type(value) == str:
                return parser.parse(value)
            return ''

        for r in range(START_ROW_AT or 1, min(STOP_ROW_AT, sheet.nrows)):
            row = sheet.row_values(r)

            # Check IN Time Must be present
            if shouldIgnore(row[0]) or shouldIgnore(row[2]) or not any(row[:4]):
                _logger.info("____ IGNORE : %s %s %s", row[0], row[1], any(row[:4]))
                ignored_lines.append(','.join(map(str, row)))
                continue

            try:
                emp_code = str(int(row[0]))
                check_in = xl_dtime(row[2])
                is_missed = False

                check_out = False
                if row[3]:
                    check_out = xl_dtime(row[3])
                else:
                    check_out = check_in
                    is_missed = True

                if check_out < check_in:
                    s = '%s :: %s :: Check Out Time `%s` Less then Check In Time `%s`' % (r, emp_code, check_out, check_in)
                    _logger.info("____ %s ", s)
                    skipped_lines.append(s)
                    continue

                _logger.info("____ Adding : %s :: %s %s", emp_code, check_in, check_out)
                file_data.append({
                    'row_index': r,
                    'emp_code': emp_code,
                    'check_in': to_naive_utc(check_in, file_tz),
                    'check_out': to_naive_utc(check_out, file_tz),
                    'is_missed': is_missed,
                })
            except Exception as e:
                line = ','.join(map(str, row[:4]))
                raise UserError(_('Please Check Row #%s\nLine : %s\nProblem : %s') % (r, line, e))
        _logger.info("____ Total Records : %s", len(file_data))
        _logger.info("____ Total Ignored : %s", len(ignored_lines))
        _logger.info("____ Total Skipped : %s", len(skipped_lines))
        return file_data, ignored_lines, skipped_lines

    def import_attendance(self):
        self.ensure_one()
        wb = xlrd.open_workbook(file_contents=base64.decodestring(self.file))

        sheet = wb.sheets()[0]
        attendance_data, ignored_lines, skipped_lines = self.parse_file(sheet)
        log, _ = self.create_attendance(attendance_data, ignored_lines, skipped_lines)
        if log:
            action = self.env.ref('hr_attendance_time.att_upload_log_action').read()[0]
            action.update({
                'res_id': log.id,
                'view_mode': 'form',
                'domain': [('id', '=', log.id)]
            })
            return action

    def create_attendance(self, attendance_data, ignored_lines, skipped_lines, name=None, file=None):
        name = name or self.name
        file = file or self.file
        attendances = Attendance = self.env['hr.attendance']
        emp_not_found = []
        _logger.info("____ Skipped Lines : %s", ignored_lines)

        cr = self.env.cr
        for att in sorted(attendance_data, key=lambda a: (a['check_in'], a['emp_code'])):
            sql = """
            SELECT id FROM hr_employee WHERE identification_id = %s LIMIT 1
            """

            cr.execute(sql, (att['emp_code'],))
            res = cr.fetchone()
            if res and res[0]:
                emp_id = res[0]
                attendances += Attendance.sudo().create({
                    'employee_id': emp_id,
                    'check_in': att['check_in'],
                    'check_out': att['check_out'],
                    'is_missed': att['is_missed']
                })
            else:
                emp_not_found.append(', '.join(map(str, att.values())))
                _logger.info("____ Employee Not Found : Row = %s, Code = %s", att['row_index'], att['emp_code'])
        log = self.env['att.upload.log']
        if attendances:
            log = log.create({
                'name': name,
                'file': file,
                # 'attendance_ids': [(4, _id) for _id in attendances.ids],
                'skipped_count': len(skipped_lines),
                'skipped_text': '\n'.join(skipped_lines),
                'ignored_count': len(ignored_lines),
                'ignored_text': '\n'.join(ignored_lines),
                'no_emp_count': len(emp_not_found),
                'no_emp_text': '\n'.join(emp_not_found),
            })
            sql = """
            UPDATE hr_attendance SET att_log_id = %s WHERE id IN %s
            """
            cr.execute(sql, (log.id, tuple(attendances.ids),))
        return log, attendances
