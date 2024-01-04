# -*- coding: utf-8 -*-
from datetime import datetime, time
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, DAILY, WEEKLY
import math
from pytz import timezone, UTC

from odoo.addons.resource.models.resource import float_to_time
from odoo import fields, models, api


def timezone_datetime(dt, tz=None, tz_name=''):
    if not dt.tzinfo:
        if not tz and tz_name:
            tz = timezone(tz_name) or UTC
        dt = dt.replace(tzinfo=tz)
    return dt


def to_naive_user_tz(datetime, tz_name):
    tz = tz_name and timezone(tz_name) or UTC
    return UTC.localize(
        datetime.replace(tzinfo=None),
        is_dst=False).astimezone(tz).replace(tzinfo=None)


def to_naive_utc(datetime, tz_name='Asia/Kolkata'):
    tz = tz_name and timezone(tz_name) or UTC
    return tz.localize(datetime.replace(tzinfo=None), is_dst=False).astimezone(
        UTC).replace(tzinfo=None)


class Attendance(models.Model):
    _inherit = "hr.attendance"

    # has_timeoff = fields.Boolean(
    #     "Business Time Off",
    #     compute="_compute_has_timeoff", store=True)
    # leave_ids = fields.Many2many(
    #     "hr.leave", string="Business Time Off on this Date",
    #     compute="_compute_has_timeoff", store=True)
    leave_id = fields.Many2one("hr.leave", string="Leave", compute="_compute_has_timeoff", store=True)
    leave_type_id = fields.Many2one(related="leave_id.holiday_status_id", store=True)
    state = fields.Selection([
        ('draft', "Draft"),
        ('worked_hours', 'Accepted Work Hours'),
        ('actual_hours', 'Consider, Scheduled Hours')], default='worked_hours')

    actual_hours = fields.Float(string="Scheduled Hours", compute="_compute_actual_hours", store=True)
    diff_hours = fields.Float("UT/OT Hours", compute="_compute_hours", store=True)
    is_week_off = fields.Boolean("Is Week Off ?", compute="_compute_actual_hours", store=True)
    final_hours = fields.Float(string="Payslip Hours", compute="_compute_final_hours", store=True)
    # late_in = fields.Float("Late Check In", compute="_compute_late", store=True)
    # early_out = fields.Float("Early Out", compute="_compute_late", store=True)
    actual_in = fields.Datetime("Actual Check In")
    actual_out = fields.Datetime("Actual Check Out")
    calendar_line_in_id = fields.Many2one("resource.calendar.attendance", string="Calendar In Line")
    public_holiday_id = fields.Many2one("resource.calendar.leaves", string="Public Holiday", compute="_compute_has_timeoff", store=True)

    att_log_id = fields.Many2one("att.upload.log", string="Attendance Log")

    department_id = fields.Many2one(related="employee_id.department_id", store=True)
    section_id = fields.Many2one(related="employee_id.section_id", store=True)
    job_id = fields.Many2one(related="employee_id.job_id", store=True)
    is_missed = fields.Boolean("Missed Checkout")

    @api.depends("state", "employee_id", "actual_hours", "worked_hours")
    def _compute_final_hours(self):
        for rec in self:
            hours = 0
            if rec.state == 'actual_hours':
                hours = rec.actual_hours
            elif rec.state == 'worked_hours':
                hours = rec.worked_hours
            rec.final_hours = hours

    @api.depends('employee_id', 'check_in', 'check_out')
    def _compute_actual_hours(self):
        combine = datetime.combine
        for rec in self:
            actual_hours = 0
            if rec.check_in and rec.check_out:
                calendar = rec.employee_id.resource_calendar_id
                # actual_hours = calendar.get_work_hours_count(
                #         combine(rec.check_in.date(), time.min),
                #         combine(rec.check_out.date(), time.max),
                #         compute_leaves=True,
                #     )

                start_date = combine(rec.check_in.date(), time.min)
                end_date = combine(rec.check_out.date(), time.max)

                if not start_date.tzinfo:
                    start_date = start_date.replace(tzinfo=UTC)
                if not end_date.tzinfo:
                    end_date = end_date.replace(tzinfo=UTC)

                intervals = calendar._work_intervals_batch(
                    start_date,
                    end_date,
                    domain=[], tz=UTC)[False]

                actual_hours = sum(
                    (stop - start).total_seconds() / 3600
                    for start, stop, meta in intervals
                )

            rec.actual_hours = actual_hours
            rec.is_week_off = actual_hours == 0

    def _compute_actual_hours_new(self):
        combine = datetime.combine
        actual_hours = 0
        if self.check_in and self.check_out:
            calendar = self.employee_id.resource_calendar_id

            start_date = combine(self.check_in.date(), time.min)
            end_date = combine(self.check_out.date(), time.max)

            if not start_date.tzinfo:
                start_date = start_date.replace(tzinfo=UTC)
            if not end_date.tzinfo:
                end_date = end_date.replace(tzinfo=UTC)

            intervals = calendar._work_intervals_batch(
                start_date,
                end_date,
                domain=[], tz=UTC)[False]

            actual_hours = sum(
                (stop - start).total_seconds() / 3600
                for start, stop, meta in intervals
            )
            return actual_hours

    @api.depends('actual_hours', 'worked_hours')
    def _compute_hours(self):
        for rec in self.filtered(lambda r: r.worked_hours):
            actual_hours = rec._compute_actual_hours_new()
            rec.diff_hours = rec.worked_hours - actual_hours

    # @api.depends('actual_in', 'actual_out', 'check_in', 'check_out')
    # def _compute_late(self):
    #     for rec in self.filtered(lambda r: r.check_in and r.check_out and r.actual_in and r.actual_out):
    #         rec.late_in = (rec.actual_in - rec.check_in).total_seconds() / 3600
    #         rec.early_out = (rec.check_out - rec.actual_out).total_seconds() / 3600

    @api.depends("check_in", "check_out", "employee_id")
    def _compute_has_timeoff(self):
        for rec in self:
            if not all([rec.check_in, rec.check_out, rec.employee_id]):
                continue
            sql = """SELECT l.id
            FROM hr_leave AS l
                LEFT JOIN hr_leave_type AS t ON l.holiday_status_id = t.id
            WHERE
                l.state = 'validate'
                AND l.employee_id = %s
                AND request_date_from <= DATE(%s) AND request_date_to >= DATE(%s)
                """
            self.env.cr.execute(sql, ((rec.employee_id.id, rec.check_in, rec.check_out)))
            result = self.env.cr.fetchall()
            leave_ids = list(map(lambda b: b[0], result))
            # rec.has_timeoff = True
            rec.leave_id = leave_ids and leave_ids[0] or False
            # rec.leave_ids = [(4, leave_id) for leave_id in leave_ids]

            sql = """
            SELECT id FROM resource_calendar_leaves
                WHERE
                    date_from <= %s AND date_to >= %s AND calendar_id = %s
                    AND resource_id is null
                LIMIT 1
            """
            self.env.cr.execute(sql, ((rec.check_in, rec.check_out, rec.employee_id.resource_calendar_id.id)))
            result = self.env.cr.fetchone()
            rec.public_holiday_id = result and result[0] or False

    def get_resource_attendance(self, start_dt, end_dt, calendar):
        domain = [
            ('calendar_id', '=', calendar.id),
            ('display_type', '=', False),
        ]
        combine = datetime.combine
        tz = timezone(calendar.tz)
        start_dt = start_dt.astimezone(tz)
        end_dt = end_dt.astimezone(tz)
        result = []
        for attendance in self.env['resource.calendar.attendance'].search(domain):
            start = start_dt.date()
            if attendance.date_from:
                start = max(start, attendance.date_from)
            until = end_dt.date()
            if attendance.date_to:
                until = min(until, attendance.date_to)
            if attendance.week_type:
                start_week_type = int(math.floor((start.toordinal()-1)/7) % 2)
                if start_week_type != int(attendance.week_type):
                    # start must be the week of the attendance
                    # if it's not the case, we must remove one week
                    start = start + relativedelta(weeks=-1)
            weekday = int(attendance.dayofweek)

            if calendar.two_weeks_calendar and attendance.week_type:
                days = rrule(WEEKLY, start, interval=2, until=until, byweekday=weekday)
            else:
                days = rrule(DAILY, start, until=until, byweekday=weekday)

            for day in days:
                # attendance hours are interpreted in the resource's timezone
                dt0 = combine(day, float_to_time(attendance.hour_from))
                dt1 = combine(day, float_to_time(attendance.hour_to))

                result.append([dt0, dt1, attendance])

        return result

    def set_late_fields(self, vals):
        keys = vals.keys()
        tz_name = self.env.user.tz or 'UTC'
        if 'check_in' in keys or 'check_out' in keys or 'employee_id' in keys:
            combine = datetime.combine
            for rec in self.filtered(lambda r: r.check_in):
                employee = rec.employee_id
                calendar = employee.resource_calendar_id
                check_in = to_naive_user_tz(rec.check_in, tz_name)
                check_out = to_naive_user_tz(rec.check_out, tz_name) if rec.check_out else check_in

                intervals = self.get_resource_attendance(check_in, check_out, calendar)
                work_intervals = sorted(intervals, key=lambda x: x[0])
                work_hours = calendar.get_work_hours_count(
                    combine(check_in.date(), time.min),
                    combine(check_out.date(), time.max),
                    compute_leaves=True,
                )
                actual_vals = {
                    'actual_hours': work_hours
                }
                for start, stop, meta in work_intervals:
                    if check_in < stop:
                        actual_vals.update({
                            'actual_in': to_naive_utc(start, tz_name),
                            'actual_out': to_naive_utc(stop, tz_name),
                            'calendar_line_in_id': meta.id,
                        })
                        break
                if work_hours != rec.worked_hours:
                    actual_vals.update({
                        'state': 'draft'
                    })
                if actual_vals:
                    rec.write(actual_vals)

    def write(self, vals):
        if vals.get('check_out'):
            vals.update({'is_missed': False})
        result = super().write(vals)
        self.set_late_fields(vals)
        return result

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record.set_late_fields(vals)
        return record

    def action_actual_hours(self):
        self.write({'state': 'actual_hours'})

    def action_worked_hours(self):
        self.write({'state': 'worked_hours'})


class Leave(models.Model):
    _inherit = "hr.leave"

    def link_attendance(self):
        cr = self.env.cr
        Attendance = self.env['hr.attendance']
        for leave in self:
            sql = """
            SELECT DISTINCT(a.id)
            FROM hr_attendance AS a
                LEFT JOIN hr_leave AS l
                    ON l.employee_id = a.employee_id
            WHERE
                a.employee_id = %s
                AND a.leave_id is null
                AND (%s, %s) OVERLAPS (DATE(a.check_in), DATE(a.check_out))
            """
            cr.execute(sql, (leave.employee_id.id, leave.request_date_from, leave.request_date_to))
            result = cr.fetchall()
            att_ids = list(map(lambda a: a[0], result))
            if att_ids:
                Attendance.sudo().browse(att_ids).write({'leave_id': leave.id, 'state': 'draft'})

    def update_leave_completion(self):
        super(Leave, self).update_leave_completion()
        self.link_attendance()
