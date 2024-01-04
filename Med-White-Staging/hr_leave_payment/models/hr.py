# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import calendar
from datetime import datetime, time
from dateutil.rrule import rrule, MONTHLY
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    payment_type = fields.Selection([
                    ('payslip', 'Payslip'),
                    ('cheque', 'By Cheque'),
                    ('encashment', 'Encashment'),
                    ('transfer', 'Transfer')], string='Payment Type')
    period_date = fields.Date('Period Date')
    payment_reference = fields.Char('Payment Reference')
    pay_days = fields.Float("Payable Days", compute="_compute_pay_days", store=True)
    pay_rate = fields.Float(compute='_compute_payment_rate', string='Pay Rate', store=True)
    payment_rate_total = fields.Float(compute='_compute_payment_rate', string='Total Payment', store=True)
    payslip_id = fields.Many2one('hr.payslip', string='Payslip')

    allow_encashment = fields.Boolean('Allow Leave Payment', related="holiday_status_id.allow_encashment")
    payslip_line_count = fields.Integer("Payslip Lines", compute='_compute_payslip_line_count')
    emp_input_id = fields.Many2one('emp.inputs', string='Emp Inputs')
    emp_input_line_count = fields.Integer("Emp Input Lines", compute='_compute_emp_input_count')

    # @api.onchange("payment_type", "request_date_from")
    # def onchagne_payment_type(self):
    #     if self.payment_type and self.payment_type != 'payslip':
    #         self.period_date = self.request_date_from

    # @api.constrains('period_date')
    # def _check_period_date(self):
    #     for leave in self:
    #         if leave.period_date and leave.period_date < fields.Date.today():
    #             raise UserError(_('Period date can not be less than today!'))

    def _compute_payslip_line_count(self):
        HrPayslipLine = self.env['hr.payslip.line']
        for leave in self:
            payslip_line_count = 0
            if leave.payslip_id:
                payslip_line_count = HrPayslipLine.search_count([
                    ('slip_id', '=', leave.payslip_id.id)
                ])
            leave.payslip_line_count = payslip_line_count

    def _compute_emp_input_count(self):
        EmpInputpLine = self.env['emp.input.line']
        for leave in self:
            emp_input_line_count = 0
            if leave.emp_input_id:
                emp_input_line_count = EmpInputpLine.search_count([
                    ('emp_input_id', '=', leave.emp_input_id.id)
                ])
            leave.emp_input_line_count = emp_input_line_count

    def action_payslip_line_view(self):
        self.ensure_one()
        return {
            'name': _('Payslip Lines'),
            'view_mode': 'tree, form',
            'res_model': 'hr.payslip.line',
            'view_id': False,
            'views': [(self.env.ref('hr_leave_payment.view_hr_payslip_line_leave_tree').id, 'tree'), (self.env.ref('hr_payroll.view_hr_payslip_line_form').id, 'form')],
            'type': 'ir.actions.act_window',
            'domain': [('slip_id', '=', self.payslip_id.id)],
            'context': {'create': False, 'edit': False},
        }

    def action_emp_input_view(self):
        self.ensure_one()
        return {
            'name': _('Emp Input Lines'),
            'view_mode': 'tree',
            'res_model': 'emp.input.line',
            'view_id': self.env.ref('hr_leave_payment.view_emp_input_line_leave_tree').id,
            'type': 'ir.actions.act_window',
            'domain': [('emp_input_id', '=', self.emp_input_id.id)],
            'context': {'create': False, 'edit': False},
        }

    @api.depends('request_date_from', 'request_date_to', 'employee_id')
    def _compute_pay_days(self):
        for leave in self:
            pay_days = 0
            if leave.request_date_from and leave.request_date_to and leave.employee_id:
                leave_from = datetime.combine(leave.request_date_from, datetime.min.time())
                leave_to = datetime.combine(leave.request_date_to, datetime.max.time())
                pay_days = leave._get_adjusted_days(leave_from, leave_to, leave.employee_id)
            leave.pay_days = pay_days

    @api.depends('request_date_to', 'employee_id', 'request_date_from')
    def _compute_payment_rate(self):
        for leave in self:
            contract = leave.employee_id.sudo().contract_id
            salary_per_day = contract.get_per_day_salary()
            leave.pay_rate = salary_per_day
            leave.payment_rate_total = leave.pay_days * salary_per_day

    def _get_adjusted_days(self, date_from, date_to, emp):
        if self.holiday_status_id.leave_type == 'sick':
            result_days = self._get_number_of_days(date_from, date_to, emp.id)['days']
        else:
            result_days = emp._get_work_days_data(date_from, date_to, compute_leaves=False)['days']
        return result_days

    def _get_plus_mins_result(self, period_date=None):
        result = {}
        minsu_result = {}
        if not period_date:
            period_date = self.period_date

        from_month = self.request_date_from.month
        to_month = self.request_date_to.month
        period_month = period_date.month

        number_of_days = self.pay_days
        if self.payment_type == 'payslip':
            if from_month == to_month == period_month:
                return [], [], 0

            if to_month != from_month:
                if from_month == period_month:
                    leave_to = datetime.combine(self.request_date_to, datetime.min.time())
                    last_month_start_date = leave_to.replace(day=1, hour=00, minute=00)
                    last_month_last_date = leave_to.replace(hour=23, minute=59)
                    number_of_days = self._get_adjusted_days(last_month_start_date, last_month_last_date, self.employee_id)
                elif to_month == period_month:
                    leave_from = datetime.combine(self.request_date_from, datetime.max.time())
                    first_month_start = leave_from.replace(hour=00, minute=00)
                    upto_day = calendar.monthrange(first_month_start.year, first_month_start.month)[1]
                    first_month_last_date = leave_from.replace(day=upto_day, hour=23, minute=59)
                    number_of_days = self._get_adjusted_days(first_month_start, first_month_last_date, self.employee_id)

        per_day_salary = self.pay_rate
        working_pos_allowance = (per_day_salary * number_of_days)  # Total Positive Calculation

        result.update({
            period_date: working_pos_allowance,
        })

        end_date_plus_one = self.request_date_to.replace(day=self.request_date_from.day)  # + relativedelta(days=+1)
        start_date_plus_one = self.request_date_from  # + relativedelta(days=-1)

        months = [dt for dt in rrule(MONTHLY, dtstart=start_date_plus_one, until=end_date_plus_one)]

        # resource_calendar = self.employee_id.resource_calendar_id

        last_month_last_date = False
        if len(months) > 1:
            last_month_last_date = months.pop(-1).replace(day=self.request_date_to.day, hour=23, minute=59)
        first_month_start_date = months.pop(0)

        # next_month_start_date = first_month_start_date + relativedelta(day=1, months=+1)
        # worked = resource_calendar.get_work_duration_data(next_month_start_date, last_month_last_date)

        # starting month calculation
        if first_month_start_date.month != period_date.month:
            upto_day = self.request_date_to.day
            if self.request_date_from.month != self.request_date_to.month:
                upto_day = calendar.monthrange(first_month_start_date.year, first_month_start_date.month)[1]
            first_month_last_date = first_month_start_date.replace(day=upto_day, hour=23, minute=59)
            first_month_leave = self._get_adjusted_days(first_month_start_date, first_month_last_date, self.employee_id)
            first_month_total = (per_day_salary * first_month_leave)
            minsu_result.update({
                first_month_start_date: first_month_total
            })

        for month in months:
            month_start_date = month.replace(day=1)
            month_end_date = month + relativedelta(day=1, months=+1)
            # Mid Month Days should be considered End Date
            if month_start_date.month != period_date.month:
                month_leave = self._get_adjusted_days(month_start_date, month_end_date, self.employee_id)
                month_total = (per_day_salary * month_leave)
                minsu_result.update({
                    month_start_date.strftime('%Y-%m-%d'): month_total
                })

        # last month calculation
        if last_month_last_date:
            upto_day = 1
            if self.request_date_from.month == self.request_date_to.month:
                upto_day = self.request_date_to.day
            last_month_start_date = last_month_last_date.replace(day=upto_day, hour=00, minute=00)
            last_month_leave = self._get_adjusted_days(last_month_start_date, last_month_last_date, self.employee_id)
            last_month_total = (per_day_salary * last_month_leave)
            if last_month_last_date.month != period_date.month:
                minsu_result.update({
                    last_month_start_date: last_month_total
                })
        return result, minsu_result, number_of_days

    def action_emp_input(self):
        # res = super(HrLeave, self).action_approve()
        EmpInput = self.env['emp.inputs']
        for leave in self.filtered('period_date'):
            from_month = leave.request_date_from.month
            to_month = leave.request_date_to.month
            period_month = leave.period_date.month

            lines = []
            if leave.payment_type and leave.payment_type != 'payslip':
                if from_month == to_month == period_month:
                    lines.append((0, 0, {
                        'payslip_date': leave.request_date_from,
                        'amount': leave.payment_rate_total * -1
                    }))
                else:
                    # InCase Two Months in Leave
                    prev_dt = leave.request_date_from - relativedelta(months=1)
                    result, minsu_result, leave_days = leave._get_plus_mins_result(prev_dt)
                    for key, value in minsu_result.items():
                        if value > 0.0:
                            lines.append((0, 0, {
                                'payslip_date': key,
                                'amount': -1 * value
                            }))

            elif leave.payment_type == 'payslip' and (from_month != to_month) or (from_month != period_month) or (to_month != period_month):
                result, minsu_result, leave_days = leave._get_plus_mins_result()
                for key, value in result.items():
                    if value > 0.0:
                        lines.append((0, 0, {
                            'payslip_date': key,
                            'amount': value
                        }))

                for key, value in minsu_result.items():
                    if value > 0.0:
                        lines.append((0, 0, {
                            'payslip_date': key,
                            'amount': -1 * value
                        }))
            if lines:
                new_emp_input = EmpInput.new({
                    'name': _("Auto Added From Leave Period Date %s" % (leave.period_date)),
                    'employee_id': leave.employee_id.id,
                    'input_type': 'alw',
                    'tot_amount': leave.payment_rate_total,
                    'no_of_installment': 1,
                    'start_date': leave.period_date,
                    'input_line_ids': lines,
                })
                new_emp_input._onchange_employee()
                emp_input_vals = new_emp_input._convert_to_write(new_emp_input._cache)
                if leave.emp_input_id:
                    emp_input = leave.emp_input_id
                    emp_input.write(emp_input_vals)
                else:
                    emp_input = EmpInput.create(emp_input_vals)
                emp_input.with_context(no_regular_installment=True).action_confirm()
                leave.write({'emp_input_id': emp_input.id})
        return True

    def validate_emp_input(self):
        if self.emp_input_id:
            if self.emp_input_id.state == 'paid':
                raise UserError(_('Cannot refuse/reset leave if linked Employee Input already paid/deducted.'))

    def action_refuse(self):
        for holiday in self:
            holiday.validate_emp_input()
            holiday.emp_input_id.action_cancel()

        return super(HrLeave, self).action_refuse()

    def action_draft(self):
        for holiday in self:
            holiday.validate_emp_input()
            holiday.emp_input_id.action_reset()
        return super(HrLeave, self).action_draft()

    def action_validate(self):
        self.action_emp_input()
        result = super(HrLeave, self).action_validate()
        return result

    def button_payslip_element(self):
        HrPayslipRun = self.env['hr.payslip.run']
        Payslip = self.env['hr.payslip']

        struct = self.env.ref('boutiqaat_hr_payslip.payroll_structure_att_pay_kuwait')
        # working_entry = self.env.ref('hr_leave_payment.work_entry_type_payment_leave')
        working_entry = self.env['hr.work.entry.type'].search([('code', '=', 'WORK100')], limit=1)

        for leave in self:
            payslip_run = HrPayslipRun.create({
                'name': self.request_date_from.strftime('%B %Y'),
                'date_start': self.request_date_from,
                'date_end': self.request_date_to,
            })

            contract = self.employee_id.sudo().contract_id
            default_values = Payslip.default_get(Payslip.fields_get())

            values = dict(default_values, **{
                'employee_id': contract.employee_id.id,
                'credit_note': payslip_run.credit_note,
                'payslip_run_id': payslip_run.id,
                'date_from': payslip_run.date_start,
                'date_to': payslip_run.date_end,
                'contract_id': contract.id,
                'struct_id': struct.id,
            })
            payslip = self.env['hr.payslip'].new(values)
            payslip._onchange_employee()
            values = payslip._convert_to_write(payslip._cache)

            payslip = Payslip.create(values)

            working_line = {
                'sequence': working_entry.sequence,
                'work_entry_type_id': working_entry.id,
                'number_of_days': leave.number_of_days,
                'number_of_hours': 0.0,
                'amount': 0,
                'payslip_id': payslip.id,
            }
            values['worked_days_line_ids'].append(working_line)
            # PayslipWorkedDays.create(working_line)
            payslip.compute_sheet()
            payslip_run.state = 'verify'
            leave.write({'payslip_id': payslip.id})


class LeaveType(models.Model):
    _inherit = 'hr.leave.type'

    allow_encashment = fields.Boolean('Allow Leave Payment')

    @api.constrains('allow_encashment', 'allocation_type')
    def _check_allocation_encash(self):
        for rec in self:
            if rec.allow_encashment and rec.allocation_type == 'no':
                raise UserError(_('Encashment allowed only for Allocatable Leave Mode.'))


class LeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    active = fields.Boolean(default=True)


class Contract(models.Model):
    _inherit = "hr.contract"

    leave_allocation = fields.Float('Leave Allocation', tracking=True)
    allocation_type = fields.Selection([
                        ('day', 'Day'),
                        ('week', 'Week'),
                        ('month', 'Month')], string='Allocation Type', tracking=True, default='month')


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def action_payslip_done(self):
        HrLeave = self.env['hr.leave']
        result = super(HrPayslip, self).action_payslip_done()
        for payslip in self:
            leaves = HrLeave.search([
                ('period_date', '>=', payslip.date_from),
                ('period_date', '<=', payslip.date_to),
                ('payslip_id', '=', False)
            ])
            leaves.write({'payslip_id': payslip.id})
        return result
