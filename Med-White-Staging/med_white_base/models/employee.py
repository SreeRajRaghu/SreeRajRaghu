
from datetime import date
from dateutil.relativedelta import relativedelta
# from pytz import timezone

import logging
# from odoo.tools.date_utils import date_range
from odoo import api, models, fields
# from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class EmpType(models.Model):
    _name = "hr.emp.type"
    _description = "HR Emp Type"

    name = fields.Char(required=True)


class EmpLevel(models.Model):
    _name = "hr.emp.level"
    _description = "HR Emp Level"

    name = fields.Char(required=True)


class EmpCertificate(models.Model):
    _name = "hr.certificate"
    _description = "HR Emp Certificate"

    name = fields.Char(required=True)


class Department(models.Model):
    _inherit = "hr.department"

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', index=True, tracking=True)

    def write(self, vals):
        res = super().write(vals)
        if vals.get('analytic_account_id'):
            Contract = self.env['hr.contract']
            for dept in self:
                contracts = Contract.search([('department_id', '=', dept.id)])
                contracts.write({'analytic_account_id': dept.analytic_account_id.id})
        return res


class Contract(models.Model):
    _inherit = "hr.contract"

    analytic_account_id = fields.Many2one(tracking=True)
    state = fields.Selection(tracking=True)

    @api.onchange('department_id')
    def _onchange_department_id(self):
        if self.department_id and self.department_id.analytic_account_id:
            self.analytic_account_id = self.department_id.analytic_account_id


    @api.model
    def update_state(self):
        self.search([
            ('state', '=', 'open'),
            ('date_end', '<=', fields.Date.to_string(date.today() + relativedelta(days=7))),
            ('date_end', '>=', fields.Date.to_string(date.today() + relativedelta(days=1))),
        ]).write({
            'kanban_state': 'blocked'
        })

        self.search([
            ('state', '=', 'open'),
            ('date_end', '<=', fields.Date.to_string(date.today() + relativedelta(days=1))),
        ]).write({
            'state': 'close'
        })

        self.search([('state', '=', 'draft'), ('kanban_state', '=', 'done'), ('date_start', '<=', fields.Date.to_string(date.today())),]).write({
            'state': 'open'
        })

        contract_ids = self.search([('date_end', '=', False), ('state', '=', 'close'), ('employee_id', '!=', False)])
        # Ensure all closed contract followed by a new contract have a end date.
        # If closed contract has no closed date, the work entries will be generated for an unlimited period.
        for contract in contract_ids:
            next_contract = self.search([
                ('employee_id', '=', contract.employee_id.id),
                ('state', 'not in', ['cancel', 'new']),
                ('date_start', '>', contract.date_start)
            ], order="date_start asc", limit=1)
            if next_contract:
                contract.date_end = next_contract.date_start - relativedelta(days=1)
                continue
            next_contract = self.search([
                ('employee_id', '=', contract.employee_id.id),
                ('date_start', '>', contract.date_start)
            ], order="date_start asc", limit=1)
            if next_contract:
                contract.date_end = next_contract.date_start - relativedelta(days=1)

        return True


class Employee(models.Model):
    _inherit = "hr.employee"

    emp_type_id = fields.Many2one("hr.emp.type", string="Employee Type")
    emp_level_id = fields.Many2one("hr.emp.level", string="Level")
    certificate_level_id = fields.Many2one("hr.certificate", 'Certificate Level')
    department_id = fields.Many2one(tracking=True)
    contract_id = fields.Many2one(tracking=True)
    contract_type = fields.Char(related="contract_id.contract_type", store=True, tracking=True)

    def write(self, vals):
        res = super().write(vals)
        if vals.get('department_id'):
            Contract = self.env['hr.contract']
            for emp in self:
                contracts = Contract.search([('employee_id', '=', emp.id)])
                contracts.write({'analytic_account_id': emp.department_id.analytic_account_id.id})
        return res

    def get_pay_amount(self, payslip, full_amount, qty, by_days=True):
        if qty == 0:
            return 0

        # calendar = payslip.contract_id.resource_calendar_id
        # date_from = payslip.date_from
        # date_to = payslip.date_to
        # is_from_mid = False

        # employee = payslip.contract_id.employee_id

        # if employee.date_joining and employee.date_joining >= payslip.date_from and employee.date_joining <= payslip.date_to:
        #     date_from = employee.date_joining
        #     # is_from_mid = True
        # if employee.date_job_end and employee.date_job_end >= payslip.date_from and employee.date_job_end <= payslip.date_to:
        #     date_to = employee.date_job_end
        #     # is_from_mid = True

        # day_from = datetime.combine(date_from, time.min)
        # day_to = datetime.combine(date_to, time.max)

        # worked = calendar.get_work_duration_data(day_from, day_to)
        # days = worked['days']
        # hours = worked['hours']

        if by_days:
            working_units = payslip.countable_working_days
            actual_units = payslip.contract_id.month_days or 26
            # if is_from_mid:
            #     actual_units = days
        else:
            working_units = payslip.countable_working_hours
            actual_units = payslip.contract_id.tot_monthly_hours or 208
            # if is_from_mid:
            #     actual_units = hours

        countable_units = working_units  # actual_units - (working_units - qty)
        per_unit = full_amount / actual_units
        _logger.info(
            "\n\nPer Unit :: Compute :: %s :: %s %s %s %s %s",
            by_days, working_units, actual_units, qty, countable_units, per_unit)
        return per_unit * countable_units

    def get_pay_amount_kuwait_payroll(self, payslip, full_amount, qty, by_days=True):
        if qty == 0:
            return 0
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
            countable_units = qty
        else:
            countable_units = actual_units - (working_units - qty)
        per_unit = full_amount / actual_units
        _logger.info(
            "\n\nPer Unit :: Compute :: %s :: %s %s %s %s %s :: From Mid %s",
            by_days, working_units, actual_units, qty, countable_units, per_unit, is_from_mid)
        return per_unit * countable_units


class EmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    emp_type_id = fields.Many2one("hr.emp.type", string="Employee Type", readonly=True)
    emp_level_id = fields.Many2one("hr.emp.level", string="Level")
    certificate_level_id = fields.Many2one("hr.certificate", 'Certificate Level')
    contract_type = fields.Char(readonly=True)
