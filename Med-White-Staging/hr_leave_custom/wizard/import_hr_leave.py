# -*- coding: utf-8 -*-

import xlrd
import base64

from odoo import fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil import parser

import logging


START_ROW_AT = 1
STOP_ROW_AT = START_ROW_AT + 20000

_logger = logging.getLogger(__name__)


class ImportEmployeeLeave(models.TransientModel):
    _name = 'import.employee.leave'
    _description = 'Import Employee Leave'

    file = fields.Binary('File')
    name = fields.Char('File Name')

    def parse_file(self, sheet):
        Type = self.env['hr.leave.type']
        Leave = self.env['hr.leave']
        file_data = []
        skipped_lines = []
        emp_not_found = []

        def xl_dtime(value):
            if type(value) == float:
                return datetime(*xlrd.xldate.xldate_as_tuple(value, sheet.book.datemode))
            elif type(value) == str:
                return parser.parse(value)
            return ''

        for r in range(START_ROW_AT or 1, min(STOP_ROW_AT, sheet.nrows)):
            row = sheet.row_values(r)
            try:
                emp_code = str(int(row[0]))
                leave_type = str(row[2].strip())
                start_date = xl_dtime(row[3])
                end_date = False
                if row[4]:
                    end_date = xl_dtime(row[4])
                else:
                    end_date = start_date

                leave_type = Type.search([('name', '=', leave_type)], limit=1)
                if not leave_type:
                    s = '%s :: %s :: Leave Type `%s` doest not exits' % (r, emp_code, leave_type)
                    skipped_lines.append(s)
                    continue

                if start_date >= end_date:
                    s = '%s :: %s :: Start Date `%s` Greater then End Date `%s`' % (r, emp_code, start_date, end_date)
                    skipped_lines.append(s)
                    continue

                sql = """
                    SELECT id FROM hr_employee WHERE identification_id = %s LIMIT 1
                """
                self.env.cr.execute(sql, (emp_code,))
                res = self.env.cr.fetchone()
                if res and res[0]:
                    emp_id = res[0]
                else:
                    result = {
                        'row_index': r,
                        'emp_code': emp_code,
                        'holiday_status_id': leave_type.id,
                        'request_date_from': start_date.strftime('%Y-%m-%d'),
                        'request_date_to': end_date.strftime('%Y-%m-%d'),
                    }
                    emp_not_found.append(', '.join(map(str, result.values())))
                    continue

                domain = [
                    ('date_from', '<', end_date),
                    ('date_to', '>', start_date),
                    ('employee_id', '=', emp_id),
                    ('state', 'not in', ['cancel', 'refuse']),
                ]
                nholidays = Leave.search_count(domain)
                if nholidays:
                    s = '%s :: You can not set 2 times off that overlaps on the same day for the same employee %s, start date %s and end date %s' % (r, emp_code, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
                    skipped_lines.append(s)
                    continue

                if not leave_type.allow_previous_leave and start_date < fields.Datetime.today():
                    s = '%s :: %s :: Leave can not be create in Previous Date :: Start Date `%s` and End Date `%s`' % (r, emp_code, start_date, end_date)
                    skipped_lines.append(s)
                    continue

                file_data.append({
                    'row_index': r,
                    'employee_id': emp_id,
                    'emp_code': emp_code,
                    'holiday_status_id': leave_type.id,
                    'request_date_from': start_date.strftime('%Y-%m-%d'),
                    'request_date_to': end_date.strftime('%Y-%m-%d'),
                })
            except Exception as e:
                line = ','.join(map(str, row[:4]))
                raise UserError(_('Please Check Row #%s\nLine : %s\nProblem : %s') % (r, line, e))
        return file_data, skipped_lines, emp_not_found

    def import_leave(self):
        self.ensure_one()
        wb = xlrd.open_workbook(file_contents=base64.decodestring(self.file))

        sheet = wb.sheets()[0]
        leave_data, skipped_lines, emp_not_found = self.parse_file(sheet)
        self.create_leave(leave_data, skipped_lines, emp_not_found)

    def create_leave(self, leave_data, skipped_lines, emp_not_found):
        leaves = self.env['hr.leave']
        name = self.name
        file = self.file

        cr = self.env.cr
        for leave in sorted(leave_data, key=lambda a: (a['request_date_from'], a['emp_code'])):
            leave_vals = {
                'employee_id': leave['employee_id'],
                'holiday_status_id': leave['holiday_status_id'],
                'request_date_from': leave['request_date_from'],
                'request_date_to': leave['request_date_to'],
            }

            leave_rec = self.env['hr.leave'].with_context(hr_work_entry_no_check=True).new(leave_vals)
            leave_rec._onchange_request_parameters()

            leave_line = self.env['hr.leave'].with_context(
                hr_work_entry_no_check=True
            ).create(leave_rec._convert_to_write(leave_rec._cache))
            leaves += leave_line

        log = self.env['att.upload.log']
        if leaves:
            log = log.create({
                'name': name,
                'file': file,
                'skipped_count': len(skipped_lines),
                'skipped_text': '\n'.join(skipped_lines),
                'no_emp_count': len(emp_not_found),
                'no_emp_text': '\n'.join(emp_not_found),
            })
            sql = """
            UPDATE hr_leave SET att_log_id = %s WHERE id IN %s
            """
            cr.execute(sql, (log.id, tuple(leaves.ids),))
