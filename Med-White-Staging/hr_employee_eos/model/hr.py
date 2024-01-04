# coding: utf-8
import calendar
from dateutil.relativedelta import relativedelta
from ast import literal_eval

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.date_utils import get_month


class HREmployeeEOS(models.Model):
    _name = "hr.employee.eos"
    _description = "HR Employee EOS"

    employee_id = fields.Many2one('hr.employee', string='Employee')
    payslip_id = fields.Many2one('hr.payslip', 'Payslip')
    eos_days_in_month = fields.Float('EOS Allowance')
    allocated_for_month = fields.Date('EOS for Month')
    eos_amount = fields.Float('EOS Amount', help='End Of Service Amount')


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    opening_balance = fields.Float('EOS Opening Balance', digits=(16, 4))
    eos_type = fields.Selection([
        ("bal", "Add Balance"), ("calc", "Calculate from Joining")],
        string="EOS Type")
    eos_ids = fields.One2many('hr.employee.eos', 'employee_id')
    eos_balance = fields.Float(compute='_compute_eos_balance', digits=(16, 4), string='EOS Balance (Days)')
    eos_deserved = fields.Float(compute='_compute_eos_deserved_amount', digits=(16, 4), string='EOS Deserved (Days)')
    eos_amount = fields.Float(compute='_compute_eos_deserved_amount', digits=(16, 4), string='EOS Amount')
    eos_deduction_amount = fields.Float('EOS Deduction Amount', digits=(16, 4))
    # eos_calculated_on = fields.Char(compute='_compute_eos_deserved_amount', string='EOS Calculated On')

    eos_tot_year_days = fields.Float("Working Total Days", compute='_compute_eos_days')
    eos_tot_leaves = fields.Float("Total Unpaid Leaves", compute='_compute_eos_days')
    eos_net_days = fields.Float("Working Net Days", compute='_compute_eos_days', help="Total Days - Unpaid Leaves")
    eos_net_year = fields.Float("Working Net Year", digits=(16, 4), compute='_compute_eos_days', help="(Total Days - Unpaid Leaves) / 365")
    eos_additional_work = fields.Float('Additional Work', digits=(16, 4))
    eos_opening_balance_days = fields.Float('EOS Opening Balance Days', digits=(16, 4))

    def _compute_eos_balance(self):
        for employee in self:
            employee.eos_balance = sum(employee.eos_ids.mapped('eos_days_in_month'))

    def print_eos_entries(self):
        self.ensure_one()
        if not self.date_job_end:
            raise UserError(_("You can not print report without Job End Date!"))
        # datas = {
        #      'ids': self.ids,
        #      'model': 'hr.employee',
        #      'active_ids': self.ids,
        # }
        return self.env.ref('hr_employee_eos.action_hr_eos_report').report_action(self)

    def _compute_eos_days(self):
        for rec in self:
            holidays = self.env['hr.leave'].search([
                ('employee_id', '=', rec.id), ('state', '=', 'validate'),
                ('holiday_status_id.include_in_eos', '=', False)
            ])
            rec.eos_tot_leaves = tot_leaves = sum(holidays.mapped('number_of_days'))
            tot_year_days = tot_days = tdiff_year = 0
            if rec.date_joining:
                end_date = rec.date_job_end or fields.Date.today()
                diff_days = end_date - rec.date_joining
                tot_year_days = diff_days.days
                tot_days = tot_year_days - tot_leaves
                tdiff_year = tot_days / 365
            rec.eos_tot_year_days = tot_year_days
            rec.eos_net_days = tot_days
            rec.eos_net_year = tdiff_year

    def generate_eos_entries(self):
        self.ensure_one()
        # contracts = self.env['hr.contract'].search([('employee_id', '=', self.id)])
        contract = self.contract_id
        if not contract:
            raise UserError(_("Current Contract Not Found."))
        if not self.date_joining:
            raise UserError(_("Joining Date Missing."))

        curr_date = self.date_joining
        end_date = self.date_job_end or fields.Date.today()

        while curr_date < end_date:
            contract.generate_month_eos(curr_date, True, False)
            curr_date = curr_date + relativedelta(months=1)

    @api.depends('date_job_end', 'job_end_reason', 'date_joining')
    def _compute_eos_deserved_amount(self):
        for emp in self:
            eos_deserved = eos_amount = 0
            if all([emp.date_job_end, emp.date_joining, emp.job_end_reason]) or emp.job_end_reason in ('resign', 'terminate'):
                eos_deserved, eos_amount = emp._calculate_eos_amount()
            emp.eos_deserved = eos_deserved
            emp.eos_amount = eos_amount

    def get_eos_deserved(self, contract, tdiff_year):
        eos_deserved = final_eos = 0
        after_5 = contract.eos_after_5_year_days * 12
        before_5 = contract.eos_bf_5_year_days * 12
        if tdiff_year >= 5:
            after5_year = tdiff_year - 5
            eos_deserved = (after_5 * after5_year) + (before_5 * 5)
        elif tdiff_year >= 0:
            eos_deserved = before_5 * tdiff_year

        # Max 18 Months EOS Applicable
        eos_deserved = min(eos_deserved, (18 * contract.month_days))

        if self.job_end_reason in ['resign']:
            if tdiff_year > 3:
                if tdiff_year > 5:
                    final_eos += eos_deserved * 0.5 * 2
                else:
                    final_eos += eos_deserved * 0.5 * (tdiff_year - 3)

            if tdiff_year > 5:
                if tdiff_year > 10:
                    final_eos += eos_deserved * 0.67 * 5
                else:
                    final_eos += eos_deserved * 0.67 * (tdiff_year - 5)

            if tdiff_year > 10:
                final_eos += eos_deserved * (tdiff_year - 10)

            # if tdiff_year >= 10:
            #     final_eos = eos_deserved
            # elif tdiff_year >= 5:
            #     final_eos = eos_deserved * 0.6667
            # elif tdiff_year >= 3:
            #     final_eos = eos_deserved * 0.5
        elif self.job_end_reason == 'terminate':
            final_eos = eos_deserved
        return final_eos

    def _calculate_eos_amount(self):
        self.ensure_one()
        eos_amount = eos_deserved = 0
        contract = self.contract_id
        if contract:
            monthly_salary = contract.get_all_allowance()
            eos_deserved = self.get_eos_deserved(contract, self.eos_net_year)
            eos_amount = min(eos_deserved * monthly_salary / (contract.month_days or 26), monthly_salary * 18)
        return eos_deserved, eos_amount

    def get_eos_report_details(self):
        Leave = self.env['hr.leave.report']
        LeaveType = self.env['hr.leave.type']
        holiday_status = LeaveType.search([('code', '=', 'ANNUAL')])
        diff_period = relativedelta(self.date_job_end, self.date_joining)
        annual_leaves = Leave.search([
            ('employee_id', '=', self.id),
            ('holiday_status_id', 'in', holiday_status.ids),
            ('state', '=', 'validate')
        ])
        annual_bal = sum(annual_leaves.mapped('number_of_days'))
        eos_opening_balance_days = 0.0

        today = fields.Date.today()
        if self.date_job_end:
            worked_days = (self.date_job_end - today).days
            if worked_days <= 0.0:
                worked_days = 0.0

            contracts = self._get_contracts(today, today, states=['open', 'close'])

            if contracts:
                working_days = 0.0
                allocation_value = contracts[0].leave_allocation
                allocation_type = contracts[0].allocation_type

                if allocation_type == 'month':
                    month_days = calendar.monthrange(self.date_job_end.year, self.date_job_end.month)[1]
                    working_days = worked_days / month_days
                elif allocation_type == 'week':
                    working_days = worked_days / 7
                elif allocation_type == 'day':
                    working_days = worked_days

                eos_opening_balance_days = self.eos_opening_balance_days
                # working_days += eos_opening_balance_days

                working_days_balance = allocation_value * working_days
                annual_bal += working_days_balance

        return {
            'diff_period': diff_period,
            'leave_bal': round(annual_bal, 2),
            'eos_opening_balance_days': eos_opening_balance_days
        }


class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    opening_balance = fields.Float('EOS Opening Balance', readonly=True)
    eos_type = fields.Selection([
        ("bal", "Add Balance"), ("calc", "Calculate from Joining")],
        string="EOS Type")
    eos_additional_work = fields.Float('Additional Work', digits=(16, 4))
    eos_deduction_amount = fields.Float('EOS Deduction Amount', digits=(16, 4))
    eos_opening_balance_days = fields.Float('EOS Opening Balance Days', digits=(16, 4))


class HRContract(models.Model):
    _inherit = 'hr.contract'

    eos_bf_5_year_days = fields.Float('EOS Before 5 Years', placeholder="eg. 1.25")
    eos_after_5_year_days = fields.Float('EOS After 5 Years', placeholder="eg. 2.5")

    def generate_month_eos(self, month_date=False, force_generate=False, filter_contracts=True, payslip_id=None):
        is_auto_allocate = literal_eval(self.env['ir.config_parameter'].sudo().get_param('hr_employee_eos.auto_allocate_eos', 'False'))
        month_date = month_date or fields.Date.today()
        if not force_generate and not is_auto_allocate:
            return

        for contract in self:
            if not contract.eos_bf_5_year_days or not contract.eos_after_5_year_days:
                # raise UserError(_("EOS Days not configured in the contract."))
                return

            month_first_day, month_last_day = get_month(month_date)

            no_of_leave_alloc_reqs = self.env['hr.employee.eos'].search_count([
                ('employee_id', '=', contract.employee_id.id),
                ('allocated_for_month', '>=', month_first_day),
                ('allocated_for_month', '<=', month_last_day),
            ])
            if not no_of_leave_alloc_reqs:
                contract._allocate_month_eos(month_date, payslip_id=payslip_id)

    def _allocate_month_eos(self, month_date, payslip_id=None):
        self.ensure_one()
        emp = self.employee_id
        eos = EndOfService = self.env['hr.employee.eos']
        if emp.date_joining:
            eos_net_year = ((month_date - emp.date_joining).days - emp.eos_tot_leaves) / 365
            eos_days = self.eos_after_5_year_days if eos_net_year > 5 else self.eos_bf_5_year_days
            eos = EndOfService.create({
                'employee_id': emp.id,
                'eos_days_in_month': eos_days,
                'allocated_for_month': month_date,
                'eos_amount': self.get_per_day_salary() * eos_days,
                'payslip_id': payslip_id,
            })
        return eos


class HRPayslip(models.Model):
    _inherit = 'hr.payslip'

    def action_payslip_done(self):
        res = super(HRPayslip, self).action_payslip_done()
        for slip in self:
            slip.contract_id.generate_month_eos(slip.date_from, force_generate=True, payslip_id=slip.id)
        return res
