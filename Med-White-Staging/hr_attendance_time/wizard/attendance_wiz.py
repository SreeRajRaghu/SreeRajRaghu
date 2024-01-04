# -*- coding: utf-8 -*-

import base64
from io import BytesIO
import xlsxwriter
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta

import logging

from odoo import fields, models, _
from odoo.tools import misc
from odoo.addons.hr_attendance_time.models.attendance import to_naive_user_tz
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ExportAttendance(models.TransientModel):
    _name = 'wizard.export.attendance'
    _description = 'Report Attendance'

    start_date = fields.Date("Start Date", required=True)
    end_date = fields.Date("End Date", required=True)

    employee_ids = fields.Many2many("hr.employee", string="Employees")
    export_data = fields.Binary()

    def get_leave_data(self, start, end, emp_ids):
        more_condition = " AND (l.request_date_from, l.request_date_to) OVERLAPS (%s, %s)"
        args = (start, end,)
        if emp_ids:
            more_condition += " AND l.employee_id IN %s"
            args += (tuple(emp_ids,),)

        sql = """
        SELECT l.employee_id, l.number_of_days, l.holiday_status_id,
        ltype.name, e.name AS emp_name, e.identification_id,
        l.request_date_from, l.request_date_to, DATE(l.date_resume), l.id, ltype.color_name
        FROM hr_leave AS l
            LEFT JOIN hr_leave_type AS ltype ON ltype.id = l.holiday_status_id
            LEFT JOIN hr_employee AS e ON e.id = l.employee_id
        WHERE l.state = 'validate'
        %s
        GROUP BY
            l.employee_id, l.holiday_status_id, ltype.name,
            e.name, e.identification_id,
            l.request_date_from, l.request_date_to, l.date_resume,
            l.number_of_days, l.id, ltype.color_name
        ORDER BY l.employee_id, l.holiday_status_id
        """ % more_condition
        self.env.cr.execute(sql, args)
        leave_data = self.env.cr.fetchall()
        leave_by_empid = {}
        for leave in leave_data:
            leave_by_empid.setdefault(leave[0], {
                'attendances': [],
                'leaves': [],
                'emp_name': leave[4],
                'emp_no': leave[5],
            })
            leave_by_empid[leave[0]]['leaves'].append({
                'total_days': leave[1],
                'holiday_status_id': leave[2],
                'holiday_status': leave[3],
                'from_date': leave[6],
                'to_date': leave[8] or leave[7],
                'leave_id': leave[9],
                'color_name': leave[10],
            })
        return leave_by_empid

    def get_att_data(self):
        # Employee = self.env['hr.employee']
        start = fields.Date.to_string(self.start_date) + " 00:00:00"
        end = fields.Date.to_string(self.end_date) + " 23:59:59"

        more_condition = "a.check_in >= %s AND a.check_out <= %s"
        args = (start, end,)
        emp_ids = self.employee_ids.ids
        if emp_ids:
            more_condition += " AND a.employee_id IN %s"
            args += (tuple(emp_ids,),)

        sql = """
            SELECT
            a.employee_id, e.name, e.identification_id AS emp_no,
            a.check_in, a.check_out, a.worked_hours,
            (a.check_in - a.actual_in) AS late_in, (a.actual_out - a.check_out) AS early_out,
            a.diff_hours, a.is_missed
        FROM hr_attendance AS a
        LEFT JOIN hr_employee AS e ON e.id = a.employee_id
        WHERE %s ORDER BY a.employee_id, a.check_in
        """ % more_condition

        self.env.cr.execute(sql, args)
        attendance_data = self.env.cr.dictfetchall()

        leave_data = self.get_leave_data(start, end, emp_ids)
        att_by_empid = {}

        for att in attendance_data:
            att_by_empid.setdefault(att['employee_id'], {
                'attendances': [],
                'leaves': [],
                'emp_no': att['emp_no'],
                'emp_name': att['name'],
            })
            att_by_empid[att['employee_id']]['attendances'].append(att)

        for emp in leave_data:
            if leave_data.get(emp) and att_by_empid.get(emp):
                att_by_empid[emp]['leaves'] += leave_data[emp]['leaves']

        emp_only_leaves = set(leave_data.keys()).difference(att_by_empid)
        for emp_id in emp_only_leaves:
            leave = leave_data.get(emp_id)
            att_by_empid.setdefault(emp_id, {
                'attendances': [],
                'leaves': [],
                'emp_no': leave['emp_no'],
                'emp_name': leave['emp_name'],
            })
            if leave:
                att_by_empid[emp_id]['leaves'] += leave['leaves']
        return att_by_empid

    def export_attendance(self):
        self.ensure_one()
        Employee = self.env['hr.employee']
        Holiday = self.env['hr.leave']
        lang_code = self.env.user.lang or 'en_US'
        date_format = self.env['res.lang']._lang_get(lang_code).date_format
        tz_name = self.env.user.tz or 'UTC'

        attendance_data = self.get_att_data()

        if not attendance_data:
            raise UserError(_('Attendance details not found for any/selected employees in given date range.'))

        lang_code = self.env.user.lang or 'en_US'
        date_format = self.env['res.lang']._lang_get(lang_code).date_format

        next_date = datetime.combine(self.start_date, datetime.min.time())
        end_date = datetime.combine(self.end_date, datetime.max.time())
        while next_date <= end_date:
            next_date_str = next_date.strftime(date_format)
            for emp_id, value in attendance_data.items():
                date_list = [val['check_in'].strftime(date_format) for val in value['attendances']]
                if next_date_str not in date_list:
                    attendance_data[emp_id]['attendances'].append({
                        'employee_id': emp_id,
                        'emp_name': value.get('emp_name'),
                        'zero': True,
                        'check_in': next_date,
                        'check_out': next_date,
                        'late_in': False,
                        'early_out': False,
                        'is_missed': False
                    })
            next_date = next_date + relativedelta(days=1)

        def get_date_format(dt):
            return dt.strftime(date_format)

        def float_to_time(float_val):
            if not float_val:
                return ""
            return misc.format_duration(float_val)

        def datetime_range(start=None, end=None):
            span = end - start
            for i in range(span.days + 1):
                yield start + timedelta(days=i)

        def get_public_holiday(global_leaves, dt):
            # return calendar.global_leave_ids.filtered(lambda rec: rec.date_from <= dt and dt <= rec.date_to)
            for global_leave in global_leaves:
                if global_leave['date_from'] <= dt and dt <= global_leave['date_to']:
                    return global_leave
            return {}

        user_from_date = get_date_format(self.start_date)
        user_to_date = get_date_format(self.end_date)

        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        style_bold_border = workbook.add_format({
            'text_wrap': False,
            'valign': 'middle',
            'bold': True,
        })
        style_bold_border_center = workbook.add_format({
            'text_wrap': False,
            'valign': 'top',
            'border': True,
            'bold': True,
            'align': 'center',
        })
        style_title = workbook.add_format({
            'text_wrap': False,
            'valign': 'top',
            'bold': True,
            'align': 'center',
        })
        # 'bg_color': '#EEEEEE'
        format_data_normal = workbook.add_format({})
        format_data_off_day = workbook.add_format({'bg_color': '#CCCCCC'})
        # formats = [format_data_normal, format_data_off_day]

        def get_format(index, color_name):
            if index > 0:
                if color_name:
                    return workbook.add_format({'bg_color': color_name})
                else:
                    return format_data_off_day
            else:
                return format_data_normal

        for emp_id, data in attendance_data.items():
            emp = Employee.browse(emp_id)
            calendar = emp.resource_calendar_id
            attendances = data.get('attendances') or {}
            emp_no = data.get('emp_no')
            emp_name = data.get('emp_name')
            worksheet = workbook.add_worksheet("%s-%s" % (emp_no, emp_name))
            worksheet.set_column("A:I", 13)
            worksheet.set_column("J:K", 20)

            row = 1
            col = 4
            # worksheet.merge_range(row, col, row, 9, _('In/Out Report From %s To %s') % (user_from_date, user_to_date), style_bold_border_center)
            worksheet.write(row, col, _('In/Out Report From %s To %s') % (user_from_date, user_to_date), style_title)

            row += 2
            col = 0
            worksheet.write(row, col, _('Name:'), style_bold_border)
            col += 1
            # worksheet.merge_range(row, col, row, col + 2, emp_name, style_bold_border)
            worksheet.write(row, col, emp_name, style_bold_border)

            col = 5
            worksheet.write(row, col, _('Department:'), style_bold_border)
            col += 1
            # worksheet.merge_range(row, col, row, col + 1, emp.department_id.name, style_bold_border)
            worksheet.write(row, col, emp.department_id.name or '', style_bold_border)

            col = 8
            worksheet.write(row, col, _('Working Hours:'), style_bold_border)
            col += 1
            worksheet.write(row, col, calendar.name, style_bold_border)

            row += 1
            col = 0
            worksheet.write(row, col, _('Number:'), style_bold_border)
            col += 1
            worksheet.write(row, col, emp_no, style_bold_border)

            col = 5
            worksheet.write(row, col, _('Job Position:'), style_bold_border)
            col += 1
            # worksheet.merge_range(row, col, row, col + 1, emp.job_id.name, style_bold_border)
            worksheet.write(row, col, emp.job_id.name or '', style_bold_border)

            row += 1

            header_line = [
                {'name': _('Date'), 'larg': 13, 'col': {}},
                {'name': _('Day'), 'larg': 13, 'col': {}},
                {'name': _('In'), 'larg': 13, 'col': {}},
                {'name': _('Out'), 'larg': 13, 'col': {}},
                {'name': _('Total'), 'larg': 13, 'col': {}},
                {'name': _('Late In'), 'larg': 13, 'col': {}},
                {'name': _('Early Out'), 'larg': 13, 'col': {}},
                {'name': _('OT'), 'larg': 13, 'col': {}},
                {'name': _('UT'), 'larg': 13, 'col': {}},
                {'name': _('Status'), 'larg': 15, 'col': {}},
            ]

            row += 2
            start_row = row
            col = 0
            for h in header_line:
                worksheet.write(row, col, h['name'], style_bold_border_center)
                col += 1

            total = tot_late_in = tot_early_out = tot_ot = tot_ot = tot_ut = 0
            working_days = calendar.attendance_ids.mapped('dayofweek')
            global_leaves = calendar.global_leave_ids.read(['name', 'date_from', 'date_to'])

            sorted_attendances = sorted(attendances, key=lambda k: k['check_in'])
            count_days = {
                'absent': 0,
                'public_holiday': 0,
                'normal': 0,
                'week_off': 0,
                'leave': 0
            }
            for att in sorted_attendances:
                check_in = to_naive_user_tz(att.get('check_in'), tz_name)
                check_out = to_naive_user_tz(att.get('check_out'), tz_name)
                format_index = 0
                leaves = data.get('leaves') or {}

                late_in_str = ''
                late_in = att.get('late_in')
                # a.check_in - a.actual_in
                if late_in:
                    late_in_sec = late_in.total_seconds() / 3600
                    if late_in_sec > 0:
                        tot_late_in += late_in_sec
                        late_in_str = float_to_time(late_in_sec)

                # a.actual_out - a.check_out
                early_out_str = ''
                early_out = att.get('early_out')
                if early_out:
                    early_out_sec = early_out.total_seconds() / 3600
                    if early_out_sec > 0:
                        tot_early_out += early_out_sec
                        early_out_str = float_to_time(early_out_sec)

                leave_type = ''
                color_name = ''
                for l in leaves:
                    dt_range = list(datetime_range(l['from_date'], l['to_date']))
                    if check_in.date() in dt_range:
                        leave_type = l['holiday_status']
                        color_name = l.get('color_name')
                        break

                public_holiday = get_public_holiday(global_leaves, att['check_in'])
                check_in_day = str(check_in.weekday())
                day_status = 'Present'

                line_format = get_format(0, '')

                # Public Holiday
                if public_holiday:
                    count_days['public_holiday'] += 1
                    format_index = 1
                    day_status = _('Public Holiday : %s') % (public_holiday['name'])
                    line_format = workbook.add_format({'bg_color': 'yellow'})

                # Leave Applied
                elif leave_type:
                    count_days['leave'] += 1
                    format_index = 1
                    day_status = leave_type
                    line_format = get_format(format_index, color_name)

                # Off Day eg. Friday
                elif check_in_day not in working_days:
                    count_days['week_off'] += 1
                    format_index = 1
                    day_status = _("Off Day")
                    line_format = get_format(1, '')

                # Absent
                elif check_in_day in working_days and att.get('zero') and not leave_type:
                    count_days['absent'] += 1
                    day_status = 'Absent'
                    line_format = workbook.add_format({'bg_color': 'black', 'font_color': 'white'})

                elif att.get('is_missed'):
                    day_status = 'Missed Checkout'
                    line_format = workbook.add_format({'bg_color': 'blue', 'font_color': 'white'})

                # Normal Days
                else:
                    count_days['normal'] += 1

                row += 1
                col = 0

                worksheet.write(row, col, get_date_format(check_in), line_format)
                col += 1
                worksheet.write(row, col, check_in.strftime("%A"), line_format)
                col += 1
                if att.get('zero'):
                    check_in = '00:00:00'
                    check_out = '00:00:00'
                    worked_hours = 0.0
                else:
                    check_in = check_in.strftime("%H:%M:%S")
                    check_out = check_out.strftime("%H:%M:%S")
                    worked_hours = att.get('worked_hours')

                worksheet.write(row, col, check_in, line_format)
                col += 1
                worksheet.write(row, col, check_out, line_format)
                col += 1
                total += att.get('worked_hours') or 0
                worksheet.write(row, col, float_to_time(worked_hours) or '00:00', line_format)
                col += 1

                worksheet.write(row, col, late_in_str, line_format)
                col += 1
                worksheet.write(row, col, early_out_str, line_format)
                col += 1
                diff_hours = att.get('diff_hours') or False
                if diff_hours > 0:
                    tot_ot += diff_hours
                else:
                    tot_ut += diff_hours
                worksheet.write(row, col, float_to_time(diff_hours > 0 and diff_hours or 0), line_format)
                col += 1
                worksheet.write(row, col, float_to_time(diff_hours < 0 and diff_hours or 0), line_format)
                col += 1
                worksheet.write(row, col, day_status, line_format)

            row += 1
            col = 4
            worksheet.write(row, col, float_to_time(total), style_bold_border_center)
            col += 1
            worksheet.write(row, col, float_to_time(tot_late_in), style_bold_border_center)
            col += 1
            worksheet.write(row, col, float_to_time(tot_early_out), style_bold_border_center)
            col += 1
            worksheet.write(row, col, float_to_time(tot_ot), style_bold_border_center)
            col += 1
            worksheet.write(row, col, float_to_time(tot_ut), style_bold_border_center)

            table = []
            for h in header_line:
                col = {}
                col['header'] = h['name']
                col.update(h['col'])
                table.append(col)

            worksheet.add_table(start_row, 0, row + 1, len(header_line) - 1, {
                'total_row': 1,
                'columns': table,
                'style': 'Table Style Light 9',
                'first_column': True,
            })

            row += 3
            for leave in leaves:
                from_date = leave['from_date']
                to_date = leave['to_date']
                leave_tot_days = leave['total_days']
                if leave_tot_days.is_integer():
                    diff = to_date - from_date
                    if leave_tot_days != diff.days:
                        leave_tot_days = diff.days
                else:
                    leave_record = Holiday.browse(leave.get('leave_id'))
                    leave_tot_days = leave_record.duration_display

                col = 0
                worksheet.write(row, col, leave['holiday_status'], style_bold_border_center)
                col += 1
                worksheet.write(row, col, leave_tot_days, style_bold_border_center)
                col += 1
                worksheet.write(row, col, from_date and from_date.strftime(date_format) or '', style_bold_border_center)
                col += 1
                worksheet.write(row, col, to_date and to_date.strftime(date_format) or '', style_bold_border_center)
                row += 1

            row += 1
            col = 0
            worksheet.write(row, col, _('Total Leave(s)'), style_bold_border_center)
            col += 1
            worksheet.write(row, col, count_days['leave'], style_bold_border_center)

            row += 2
            col = 0
            worksheet.write(row, col, _('Public Holiday(s)'), style_bold_border_center)
            col += 1
            worksheet.write(row, col, count_days['public_holiday'], style_bold_border_center)
            row += 1
            col = 0
            worksheet.write(row, col, _('Off Days'), style_bold_border_center)
            col += 1
            worksheet.write(row, col, count_days['week_off'], style_bold_border_center)
            row += 1
            col = 0
            worksheet.write(row, col, _('Absent'), style_bold_border_center)
            col += 1
            worksheet.write(row, col, count_days['absent'], style_bold_border_center)
            row += 1
            col = 0
            worksheet.write(row, col, _('Present'), style_bold_border_center)
            col += 1
            worksheet.write(row, col, count_days['normal'], style_bold_border_center)

            row += 2
            col = 0
            worksheet.write(row, col, _('Total'), style_bold_border_center)
            col += 1
            worksheet.write(row, col, sum(count_days.values()), style_bold_border_center)

        workbook.close()
        export_data = base64.b64encode(fp.getvalue())
        fp.close()
        self.write({"export_data": export_data})

        file_name = "Attendance.xlsx"
        return {
            'target': 'new',
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s/%s/%s/%s'
            % (self._name, self.id, 'export_data', file_name),
        }
