
from datetime import datetime, time, timedelta
from pytz import timezone

import logging
from odoo.tools.date_utils import date_range
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Payslip(models.Model):
    _inherit = 'hr.payslip'

    department_id = fields.Many2one("hr.department", string="Department")
    mobile = fields.Char("Mobile")
    phone = fields.Char("Phone")
    identification_id = fields.Char("Employee Number")
    calendar_working_days = fields.Float("Working Days of the Month", compute="_compute_calendar_working_days")
    calendar_working_hours = fields.Float("Working Hours of the Month", compute="_compute_calendar_working_days")
    countable_working_days = fields.Float("Countable Working Days", compute="_compute_calendar_working_days")
    countable_working_hours = fields.Float("Countable Working Hours", compute="_compute_calendar_working_days")

    @api.depends(
        'employee_id', 'contract_id', 'date_from', 'date_to', 'worked_days_line_ids',
        'worked_days_line_ids.number_of_days', 'worked_days_line_ids.number_of_hours')
    def _compute_calendar_working_days(self):
        for rec in self:
            days = 26
            hours = 208
            w_days = w_hours = 0

            if rec.employee_id and rec.contract_id and rec.date_from and rec.date_to:
                calendar = rec.employee_id.resource_calendar_id
                actual_days = rec.contract_id.month_days or 26
                actual_hours = rec.contract_id.tot_monthly_hours or 208

                date_from = rec.date_from
                date_to = rec.date_to
                is_from_mid = False

                if rec.employee_id.date_joining and rec.employee_id.date_joining >= rec.date_from and rec.employee_id.date_joining <= rec.date_to:
                    date_from = rec.employee_id.date_joining
                    is_from_mid = True
                if rec.employee_id.date_job_end and rec.employee_id.date_job_end >= rec.date_from and rec.employee_id.date_job_end <= rec.date_to:
                    date_to = rec.employee_id.date_job_end
                    is_from_mid = True

                day_from = datetime.combine(date_from, time.min)
                day_to = datetime.combine(date_to, time.max)

                worked = calendar.get_work_duration_data(day_from, day_to)
                days = worked['days']
                hours = worked['hours']
                if is_from_mid:
                    actual_days = days
                    actual_hours = hours

                worked_lines = rec.worked_days_line_ids.filtered(lambda r: r.code == "WORK100")
                days_qty = sum(worked_lines.mapped('number_of_days'))
                if days_qty:
                    w_days = actual_days - (days - days_qty)

                hours_qty = sum(worked_lines.mapped('number_of_hours'))
                if hours_qty:
                    w_hours = actual_hours - (hours - hours_qty)

            rec.calendar_working_days = days
            rec.calendar_working_hours = hours
            rec.countable_working_days = w_days
            rec.countable_working_hours = w_hours

    @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
    def _onchange_employee(self):
        emp = self.employee_id
        if emp:
            self.department_id = emp.department_id
            self.mobile = emp.mobile_phone
            self.phone = emp.phone
            self.identification_id = emp.identification_id
        return super(Payslip, self)._onchange_employee()

    def _get_new_worked_days_lines(self):
        if self.struct_id.use_worked_day_lines:
            return super(Payslip, self)._get_new_worked_days_lines()
        else:
            worked_days_line_values = self._get_attenedance_day_lines()
            worked_days_lines = self.worked_days_line_ids.browse([])
            for r in worked_days_line_values:
                worked_days_lines |= worked_days_lines.new(r)
            return worked_days_lines

    def _get_attenedance_day_lines(self):
        """
        @param contract: Browse record of contracts
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        res = []
        date_from, date_to = self.date_from, self.date_to
        contract = self.contract_id
        hours_per_day = contract.hours_per_day
        calendar = contract.resource_calendar_id
        if calendar:
            struct_type = self.struct_id.type_id
            unpaid_work_entry_types = self.struct_id.unpaid_work_entry_type_ids.ids
            def_work_entry_type = struct_type.default_work_entry_type_id
            # fill only if the contract as a working schedule linked
            day_from = datetime.combine(date_from, time.min)
            day_to = datetime.combine(date_to, time.max)

            # compute leave days
            leaves = {}
            tz = timezone(calendar.tz)
            day_leave_intervals = contract.employee_id.list_leaves(day_from, day_to, calendar=calendar)
            working_hours = 0
            working_days = 0

            working_days_list = []
            non_working_days_list = []

            for day, hours, leave in day_leave_intervals:
                holiday = leave.holiday_id
                holiday_status = holiday.holiday_status_id
                # if holiday.payment_type and holiday.payment_type != 'payslip':
                #     continue

                working_days_list.append(day)

                work_hours = calendar.get_work_hours_count(
                    tz.localize(datetime.combine(day, time.min)),
                    tz.localize(datetime.combine(day, time.max)),
                    compute_leaves=False,
                )
                work_entry_type = holiday_status.work_entry_type_id
                is_paid = work_entry_type.id not in unpaid_work_entry_types
                if is_paid or not work_entry_type:
                    working_hours += hours
                    working_days += hours / work_hours

                    if not work_entry_type:
                        work_entry_type = struct_type.def_got_work_entry_type_id

                if work_entry_type:
                    current_leave_struct = leaves.setdefault(work_entry_type.id, {
                        'number_of_days': 0.0,
                        'number_of_hours': 0.0,
                        'contract_id': contract.id,
                        'sequence': work_entry_type.sequence,
                        'work_entry_type_id': work_entry_type.id,
                        # 'amount': hours * paid_amount / total_hours if is_paid else 0,
                    })

                    if is_paid:
                        hours = -1 * hours
                    current_leave_struct['number_of_hours'] += hours
                    if work_hours:
                        current_leave_struct['number_of_days'] += hours / work_hours

            def get_dates(start, end):
                all_dates = []
                for i in range((end - start).days + 1):
                    all_dates.append(start + timedelta(days=i))
                return all_dates

            domain = [
                    ('holiday_status_id.leave_type', '=', 'sick'),
                    ('employee_id', '=', self.employee_id.id),
                    ('state', '=', 'validate'),
                    ('request_date_from', '>=', date_from),
                    ('request_date_to', '<=', date_to),
                    ('payment_type', 'in', ['payslip', False])
                ]
            sick_leaves = self.env['hr.leave'].search(domain)

            if sick_leaves:
                for d in get_dates(date_from, date_to):
                    if d not in working_days_list:
                        non_working_days_list.append(d)

                for s_leave in sick_leaves:
                    tot_sic_days = 0
                    dt_range = get_dates(s_leave.request_date_from, s_leave.request_date_to)
                    for d in dt_range:
                        if d in non_working_days_list:
                            tot_sic_days += 1

                    work_entry_type = s_leave.holiday_status_id.work_entry_type_id
                    current_leave_struct = leaves.get(work_entry_type.id)
                    if tot_sic_days and current_leave_struct:
                        tot_sic_days = tot_sic_days * -1
                        tot_sic_hours = tot_sic_days * hours_per_day
                        current_leave_struct['number_of_hours'] += tot_sic_hours
                        current_leave_struct['number_of_days'] += tot_sic_days
                        # working_hours += abs(tot_sic_hours)
                        # working_days += abs(tot_sic_days)

            # compute worked days
            regular_days, week_off_days, public_holidays = self.get_attendance_data()

            if True:
                actual_hours = 0
                actual_days = 0
                regular_ot = 0
                for day in regular_days:
                    att_hours = day[day['state']]
                    actual_hours += min(att_hours, day['actual_hours'])
                    if day['actual_hours']:
                        actual_days += 1
                    rot = att_hours - day['actual_hours']
                    if rot > 0:
                        regular_ot += rot
                res.append({
                    'number_of_days': actual_days + working_days,
                    'number_of_hours': actual_hours + working_hours,
                    'contract_id': contract.id,
                    'sequence': def_work_entry_type.sequence,
                    'work_entry_type_id': def_work_entry_type.id,
                })

                if regular_ot:
                    ttype = struct_type.def_rot_work_entry_type_id
                    res.append({
                        'number_of_days': regular_ot / (hours_per_day or 1),
                        'number_of_hours': regular_ot,
                        'contract_id': contract.id,
                        'sequence': ttype.sequence,
                        'work_entry_type_id': ttype.id,
                    })

            if week_off_days:
                hours = sum(map(lambda a: a['hours'], week_off_days))
                if not hours:
                    hours = len(week_off_days) * hours_per_day
                ttype = struct_type.def_wot_work_entry_type_id
                res.append({
                    'number_of_days': len(week_off_days),
                    'number_of_hours': hours,
                    'contract_id': contract.id,
                    'sequence': ttype.sequence,
                    'work_entry_type_id': ttype.id,
                })
            if public_holidays:
                hours = sum(map(lambda a: a['hours'], public_holidays))
                if not hours:
                    hours = len(public_holidays) * hours_per_day
                ttype = struct_type.def_pot_work_entry_type_id
                res.append({
                    'number_of_days': len(public_holidays),
                    'number_of_hours': hours,
                    'contract_id': contract.id,
                    'sequence': ttype.sequence,
                    'work_entry_type_id': ttype.id,
                })

            res.extend(leaves.values())
        return res

    def get_attendance_data(self):
        sql = """
        SELECT
            CASE WHEN state = 'worked_hours'
                THEN COALESCE(sum(worked_hours), 0) ELSE COALESCE(sum(actual_hours), 0)
                END AS hours,
            COALESCE(sum(worked_hours), 0) As worked_hours, COALESCE(sum(actual_hours), 0) AS actual_hours,
            public_holiday_id,
            COALESCE(sum(worked_hours - actual_hours), 0) AS diff, state
            FROM hr_attendance
            WHERE
                employee_id = %s AND state != 'draft'
                AND DATE(check_in) >= %s AND DATE(check_out) <= %s
            GROUP BY employee_id, state, check_in, public_holiday_id, id
        """
        self.env.cr.execute(sql, (self.employee_id.id, self.date_from, self.date_to))
        result = self.env.cr.dictfetchall()
        week_off_days = []
        public_holidays = []
        regular_days = []
        for day in result:
            if day['public_holiday_id']:
                public_holidays.append(day)
            elif not day['actual_hours']:
                week_off_days.append(day)
            else:
                regular_days.append(day)

        _logger.info('___ week_off_days : %s :: %s', len(week_off_days), week_off_days)
        _logger.info('___ regular_days : %s :: %s', len(regular_days), regular_days)
        _logger.info('___ public_holidays : %s :: %s', len(public_holidays), public_holidays)

        return regular_days, week_off_days, public_holidays

    def action_payslip_done(self):
        for payslip in self:
            domain = [
                ('date_from', '<=', payslip.date_to),
                ('date_to', '>=', payslip.date_from),
                ('employee_id', '=', payslip.employee_id.id),
                ('id', '!=', payslip.id),
                ('state', 'in', ('verify', 'done')),
            ]
            if payslip.is_refund:
                domain.append(('is_refund', '=', True))
            already_payslips = self.search(domain)
            if already_payslips:
                raise ValidationError(_("For given period and employee already paylsip exits!"))
        result = super(Payslip, self).action_payslip_done()
        return result


class PayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    currency_id = fields.Many2one(
                    'res.currency',
                    string='Currency',
                    default=lambda x: x.env.company.currency_id)


class Employee(models.Model):
    _inherit = "hr.employee"

    def get_pay_amount(self, payslip, full_amount, qty, by_days=True):
        if qty == 0:
            return 0

        calendar = payslip.contract_id.resource_calendar_id
        date_from = payslip.date_from
        date_to = payslip.date_to
        # is_from_mid = False

        employee = payslip.contract_id.employee_id

        if employee.date_joining and employee.date_joining >= payslip.date_from and employee.date_joining <= payslip.date_to:
            date_from = employee.date_joining
            # is_from_mid = True
        if employee.date_job_end and employee.date_job_end >= payslip.date_from and employee.date_job_end <= payslip.date_to:
            date_to = employee.date_job_end
            # is_from_mid = True

        day_from = datetime.combine(date_from, time.min)
        day_to = datetime.combine(date_to, time.max)

        worked = calendar.get_work_duration_data(day_from, day_to)
        days = worked['days']
        # hours = worked['hours']

        print ("days:::::::::::::", days)

        if by_days:
            working_units = payslip.countable_working_days
            actual_units = payslip.contract_id.month_days or 26
            # if is_from_mid:
            #     actual_units = days
        else:
            working_units = payslip.countable_working_hours
            actual_units = payslip.contract_id.tot_monthly_hours or 208
            print ("actual_units:::::::", actual_units)
            # if is_from_mid:
            #     actual_units = hours

        countable_units = working_units  # actual_units - (working_units - qty)
        print ("countable_units::::::::::", countable_units)
        print ("full_amount:::::::::", full_amount, actual_units)
        per_unit = full_amount / actual_units
        print ("per_unit:::::::::::", per_unit)
        _logger.info(
            "\n\nPer Unit :: Compute :: %s :: %s %s %s %s %s",
            by_days, working_units, actual_units, qty, countable_units, per_unit)
        return per_unit * countable_units

    def get_pay_amount_kuwait_payroll(self, payslip, full_amount, qty, by_days=True):
        if qty == 0:
            return 0
        orig_qty = qty
        # calendar = payslip.contract_id.resource_calendar_id
        # date_from = payslip.date_from
        # date_to = payslip.date_to
        is_from_mid = False

        employee = payslip.contract_id.employee_id

        if employee.date_joining and employee.date_joining >= payslip.date_from and employee.date_joining <= payslip.date_to:
            # date_from = employee.date_joining
            is_from_mid = True
        if employee.date_job_end and employee.date_job_end >= payslip.date_from and employee.date_job_end <= payslip.date_to:
            # date_to = employee.date_job_end
            is_from_mid = True

        # day_from = datetime.combine(date_from, time.min)
        # day_to = datetime.combine(date_to, time.max)

        # worked = calendar.get_work_duration_data(day_from, day_to)
        # days = worked['days']
        # hours = worked['hours']

        if by_days:
            working_units = payslip.calendar_working_days
            actual_units = payslip.contract_id.month_days or 26
            # if is_from_mid:
            #     actual_units = days
        else:
            working_units = payslip.calendar_working_hours
            actual_units = payslip.contract_id.tot_monthly_hours or 208
            # if is_from_mid:
            #     actual_units = hours

        # leave_lines = payslip.worked_days_line_ids.filtered(lambda r: r.code == "LEAVE90")
        # leave_days_qty = sum(leave_lines.mapped('number_of_days'))
        # print ("leave_days_qty::::", leave_days_qty)
        if actual_units < qty:
            qty = actual_units

        if actual_units < working_units:
            working_units = actual_units

        if is_from_mid:
            countable_units = orig_qty
        else:
            countable_units = actual_units - (working_units - qty)
        per_unit = full_amount / actual_units
        _logger.info(
            "\n\nPer Unit :: Compute :: %s :: %s %s %s %s %s :: From Mid %s",
            by_days, working_units, actual_units, qty, countable_units, per_unit, is_from_mid)
        return per_unit * countable_units

    def get_sick_leave_ded(self, payslip, qty, contract):
        e_qty = self.sick_leave_days_in_cur_year
        prev_qty = e_qty - qty

        balance = prev_qty

        if e_qty <= 15:
            return 0

        ded_amount = 0
        per_day = contract.get_per_day_salary()

        while balance != e_qty:
            balance += 1

            if balance < 16:
                continue

            elif balance < 26:
                ded_amount += per_day * 0.25

            elif balance < 36:
                ded_amount += per_day * 0.5

            elif balance <= 45:
                ded_amount += per_day * 0.75

            else:
                ded_amount += per_day
        return ded_amount * -1
