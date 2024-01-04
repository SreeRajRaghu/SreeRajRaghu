# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from pytz import timezone, UTC
from datetime import datetime, time

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
_logger = logging.getLogger(__name__)


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    validation_type = fields.Selection(selection_add=[
                            ('multiple', 'Mutliple Approval')])
    approver_ids = fields.One2many('hr.leave.approver', 'leave_type_id', string='Leave Approvers')
    resumer_ids = fields.One2many('hr.leave.resumer', 'leave_type_id', string='Leave Resumers')

    # allocation_type = fields.Selection(
    #     selection_add=[('auto', 'Auto Allocate based on Contract')],
    #     help='\tNo Allocation Needed: no allocation by default, users can freely request time off;'
    #          '\tFree Allocation Request: allocated by HR and users can request time off and allocations;'
    #          '\tAllocated by HR only: allocated by HR and cannot be bypassed; users can request time off;'
    #          '\tAuto Allocate based on Contract: Leaves will be allocated from Contract;')
    is_resume_date_required = fields.Boolean('Is Resume Date Required?')
    allow_previous_leave = fields.Boolean('Is Previous Date Leave Allowed ?')
    is_auto_allocate = fields.Boolean('Is Auto Allocate?')
    auto_allocation_date = fields.Date('Auto Allocation Date')

    # def action_cron_allocation(self):
    #     print ('___ self : ', self)


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    leave_approval_history_ids = fields.One2many('hr.leave.approval.history', 'hr_leave_id', string='Leave Approval History')
    leave_resume_history_ids = fields.One2many('hr.leave.resume.history', 'hr_leave_id', string='Leave Resume History')
    is_show_approve = fields.Boolean(compute='compute_show_approve', string='Is Show Approve?')
    date_resume = fields.Datetime('Resume Date')
    leave_reason = fields.Text('Reason')
    allocation_request_id = fields.Many2one('hr.leave.allocation', string='Allocation Request')
    leave_request_id = fields.Many2one('hr.leave', string='Leave Request')
    resume_days = fields.Float('Resume Days', readonly=True)
    is_show_resume = fields.Boolean(compute='compute_show_resume', string='Is Show Resume?')
    is_resume = fields.Boolean('Resume')
    is_employee_resume = fields.Boolean('Is Employee Resumed?')
    leave_resume_date = fields.Date(
                        'Leave Resume Date',
                        readonly=True,
                        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    is_resume_date_required = fields.Boolean('Is Resume Date Required?')
    att_log_id = fields.Many2one("att.upload.log", string="Attendance Log")

    @api.constrains('request_date_from')
    def _check_request_date_from(self):
        for leave in self:
            if not leave.holiday_status_id.allow_previous_leave and leave.request_date_from < fields.Date.today():
                raise UserError(_('Leave cannot be created in previous date!'))

    @api.constrains('state', 'number_of_days', 'holiday_status_id')
    def _check_holidays(self):
        # Customer Req.
        # No Need Balance Condition, but still needs to Allocate Balance.
        pass

        # for holiday in self:
        #     if holiday.holiday_type != 'employee' or not holiday.employee_id or holiday.holiday_status_id.allocation_type == 'no':
        #         continue
        #     leave_days = holiday.holiday_status_id.get_days(holiday.employee_id.id)[holiday.holiday_status_id.id]
        #     if float_compare(leave_days['remaining_leaves'], 0, precision_digits=2) == -1 or float_compare(leave_days['virtual_remaining_leaves'], 0, precision_digits=2) == -1:
        #         raise ValidationError(_('The number of remaining time off is not sufficient for this time off type.\n'
        #                                 'Please also check the time off waiting for validation.'))
    # @api.depends('number_of_days')
    # def _compute_number_of_days_display(self):
    #     for holiday in self:
    #         if holiday.holiday_status_id.leave_type == 'sick':
    #             days = (holiday.request_date_to - holiday.request_date_from).days + 1
    #         else:
    #             days = holiday.number_of_days
    #         holiday.number_of_days_display = days

    @api.onchange('date_from', 'date_to', 'employee_id')
    def _onchange_leave_dates(self):
        if self.date_from and self.date_to and self.holiday_status_id.leave_type == 'sick':
            self.number_of_days = (self.request_date_to - self.request_date_from).days + 1
        else:
            super(HrLeave, self)._onchange_leave_dates()

    def _get_number_of_days(self, date_from, date_to, employee_id):
        if self.holiday_status_id.leave_type == 'sick':
            days = (date_to - date_from).days + 1
            employee = self.env['hr.employee'].browse(employee_id)
            result = {
                'days': days,
                'hours': days * (employee.contract_id.hours_per_day or 8)
            }
        else:
            # result = super(HrLeave, self)._get_number_of_days(date_from, date_to, employee_id, compute_leave)
            if employee_id:
                employee = self.env['hr.employee'].browse(employee_id)
                return employee._get_work_days_data(date_from, date_to)

            comp_resource = self.env.company.resource_calendar_id

            today_hours = comp_resource.get_work_hours_count(
                datetime.combine(date_from.date(), time.min),
                datetime.combine(date_from.date(), time.max),
                False)

            hours = comp_resource.get_work_hours_count(date_from, date_to)

            result = {
                'days': hours / (today_hours or 8),
                'hours': hours
            }
        return result

    @api.constrains('leave_resume_date')
    def _check_resume_date(self):
        for leave in self:
            if leave.leave_resume_date and leave.leave_resume_date < leave.request_date_to:
                raise ValidationError(_('Resume date should be great than leave last date!'))

    def _get_number_leave_days(self, date_from, date_to, employee_id):
        if employee_id:
            employee = self.env['hr.employee'].browse(employee_id)
            return employee._get_work_days_data(date_from, date_to, compute_leaves=False)

        today_hours = self.env.company.resource_calendar_id.get_work_hours_count(
            datetime.combine(date_from.date(), time.min),
            datetime.combine(date_from.date(), time.max),
            False)
        hours = self.env.company.resource_calendar_id.get_work_hours_count(date_from, date_to)
        return {'days': hours / (today_hours or 8), 'hours': hours}

    def compute_show_approve(self):
        Employee = self.env['hr.employee']
        for leave in self:
            show_leave = True
            if leave.holiday_status_id.validation_type == 'multiple':
                remain_approvals = leave.leave_approval_history_ids.filtered(lambda x: not x.is_approve)
                if remain_approvals:
                    if len(remain_approvals) == 1:
                        current_remain_approval = remain_approvals
                    else:
                        current_remain_approval = remain_approvals[0]
                    if current_remain_approval:
                        current_user_employee = Employee.search([('user_id', '=', self.env.user.id)], limit=1)
                        if current_remain_approval.approver_type == 'coach' and current_user_employee != leave.employee_id.coach_id:
                            show_leave = False
                        elif current_remain_approval.approver_type == 'manager' and current_user_employee != leave.employee_id.parent_id:
                            show_leave = False
                        elif current_remain_approval.approver_type == 'dept_manager' and current_user_employee != leave.employee_id.department_id.manager_id:
                            show_leave = False
                        elif current_remain_approval.approver_type == 'hr_admin_manager' and not self.env.user.has_group('hr_leave_custom.group_hr_admin_manager'):
                            show_leave = False
                        elif current_remain_approval.approver_type == 'hr_admin_officer' and not self.env.user.has_group('hr_leave_custom.group_hr_admin_officer'):
                            show_leave = False
                        elif current_remain_approval.approver_type == 'hr_admin_admin' and not self.env.user.has_group('hr_holidays.group_hr_holidays_manager'):
                            show_leave = False
                        elif current_remain_approval.approver_type == 'hr_group' and current_user_employee not in current_remain_approval.group_id.emp_approve_ids:
                            show_leave = False

            leave.is_show_approve = show_leave

    def compute_show_resume(self):
        Employee = self.env['hr.employee']
        for leave in self:
            show_resume = True
            current_user_employee = Employee.search([('user_id', '=', self.env.user.id)], limit=1)
            if current_user_employee != leave.employee_id and not leave.is_employee_resume:
                show_resume = False

            if leave.holiday_status_id and leave.is_employee_resume:
                remain_approvals = leave.leave_resume_history_ids.filtered(lambda x: not x.is_approve)
                if remain_approvals:
                    if len(remain_approvals) == 1:
                        current_remain_approval = remain_approvals
                    else:
                        current_remain_approval = remain_approvals[0]
                    if current_remain_approval:
                        if current_remain_approval.approver_type == 'coach' and current_user_employee != leave.employee_id.coach_id:
                            show_resume = False
                        elif current_remain_approval.approver_type == 'manager' and current_user_employee != leave.employee_id.parent_id:
                            show_resume = False
                        elif current_remain_approval.approver_type == 'dept_manager' and current_user_employee != leave.employee_id.department_id.manager_id:
                            show_resume = False
                        elif current_remain_approval.approver_type == 'hr_admin_manager' and not self.env.user.has_group('hr_leave_custom.group_hr_admin_manager'):
                            show_resume = False
                        elif current_remain_approval.approver_type == 'hr_admin_officer' and not self.env.user.has_group('hr_leave_custom.group_hr_admin_officer'):
                            show_resume = False
                        elif current_remain_approval.approver_type == 'hr_admin_admin' and not self.env.user.has_group('hr_holidays.group_hr_holidays_manager'):
                            show_resume = False
                        elif current_remain_approval.approver_type == 'hr_group' and current_user_employee not in current_remain_approval.group_id.emp_approve_ids:
                            show_resume = False

            leave.is_show_resume = show_resume

    def get_approvral_user(self, approval):
        user_ids = []
        if approval.approver_type == 'coach':
            user_ids.append(self.employee_id.coach_id.user_id.id)
        elif approval.approver_type == 'manager':
            user_ids.append(self.employee_id.parent_id.user_id.id)
        elif approval.approver_type == 'dept_manager':
            user_ids.append(self.employee_id.department_id.manager_id.user_id.id)
        elif approval.approver_type == 'hr_admin_manager':
            admin_manager = self.env.ref('hr_leave_custom.group_hr_admin_manager')
            user_ids += admin_manager.users.ids
        elif approval.approver_type == 'hr_admin_officer':
            admin_officer = self.env.ref('hr_leave_custom.group_hr_admin_officer')
            user_ids += admin_officer.users.ids
        elif approval.approver_type == 'hr_admin_admin':
            holidays_manager = self.env.ref('hr_holidays.group_hr_holidays_manager')
            user_ids += holidays_manager.users.ids
        elif approval.approver_type == 'hr_group':
            approval_users = approval.group_id.emp_approve_ids.mapped('user_id').ids
            user_ids += approval_users
        return user_ids

    def _send_time_off_notification(self):
        # sending notification for first approver
        start = UTC.localize(self.date_from).astimezone(timezone(self.employee_id.tz or 'UTC'))
        end = UTC.localize(self.date_to).astimezone(timezone(self.employee_id.tz or 'UTC'))

        note = _('New %s Timeoff Request for %s from %s to %s you have to approve!') % (self.holiday_status_id.name, self.employee_id.name, start, end)
        remain_approvals = self.leave_approval_history_ids.filtered(lambda x: not x.is_approve)
        if remain_approvals:
            current_remain_approval = remain_approvals[0]
            user_ids = self.get_approvral_user(current_remain_approval)
            for user_id in user_ids:
                self.activity_schedule(
                    'hr_holidays.mail_act_leave_approval',
                    note=note,
                    user_id=user_id)

    @api.model
    def create(self, vals):
        result = super(HrLeave, self).create(vals)
        result._send_time_off_notification()
        return result

    @api.onchange('holiday_status_id')
    def onchange_holiday_status_id(self):
        self.leave_approval_history_ids = False
        self.leave_resume_history_ids = False
        if self.holiday_status_id:
            self.is_resume_date_required = self.holiday_status_id.is_resume_date_required
            if self.holiday_status_id.validation_type == 'multiple':
                approval_list = []
                resume_list = []
                for line in self.holiday_status_id.approver_ids:
                    approval_list.append((0, 0, {
                        'sequence': line.sequence,
                        'approver_type': line.approver_type,
                        'group_id': line.group_id,
                    }))
                self.leave_approval_history_ids = approval_list
                for line in self.holiday_status_id.resumer_ids:
                    resume_list.append((0, 0, {
                        'sequence': line.sequence,
                        'approver_type': line.approver_type,
                        'group_id': line.group_id,
                    }))
                self.leave_resume_history_ids = resume_list
                if resume_list:
                    self.is_employee_resume = True

    def action_approve(self):
        # if validation_type == 'both': this method is the first approval approval
        # if validation_type != 'both': this method calls action_validate() below
        if any(holiday.state != 'confirm' for holiday in self):
            raise UserError(_('Time off request must be confirmed ("To Approve") in order to approve it.'))

        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        self.filtered(lambda hol: hol.validation_type == 'both').write({'state': 'validate1', 'first_approver_id': current_employee.id})

        for holiday in self.filtered(lambda r: r.validation_type == 'multiple'):
            remain_approvals = holiday.leave_approval_history_ids.filtered(lambda x: not x.is_approve)
            if remain_approvals:
                if len(remain_approvals) == 1:
                    current_remain_approval = remain_approvals
                    current_remain_approval.write({
                        'approved_by_id': self.env.uid,
                        'approved_time': fields.Datetime.now(),
                        'is_approve': True,
                    })
                else:
                    current_remain_approval = remain_approvals[0]
                    current_remain_approval.write({
                        'approved_by_id': self.env.uid,
                        'approved_time': fields.Datetime.now(),
                        'is_approve': True,
                    })
                    holiday._send_time_off_notification()
                    return True

        # Post a second message, more verbose than the tracking message
        for holiday in self.filtered(lambda holiday: holiday.employee_id.user_id):
            holiday.message_post(
                body=_('Your %s planned on %s has been accepted' % (holiday.holiday_status_id.display_name, holiday.date_from)),
                partner_ids=holiday.employee_id.user_id.partner_id.ids)

        self.filtered(lambda hol: not hol.validation_type == 'both').action_validate()
        if not self.env.context.get('leave_fast_create'):
            self.activity_update()
        return True

    def action_resume(self):
        action = self.env.ref('hr_leave_custom.action_resume_work_wizard').read()[0]
        action['context'] = self.env.context
        return action

    def action_draft(self):
        res = super(HrLeave, self).action_draft()
        self.leave_approval_history_ids.write({'is_approve': False})
        self.leave_resume_history_ids.write({'is_approve': False})
        self.write({'is_employee_resume': False})
        return res


class HrLeaveApprover(models.Model):
    _name = 'hr.leave.approver'
    _description = 'HR Leave Approver'
    _order = 'sequence'

    sequence = fields.Integer('Sequence', required=True)
    approver_type = fields.Selection([
                    ('coach', 'By Coach'),
                    ('manager', 'By Manager'),
                    ('dept_manager', 'By Department Manager'),
                    ('hr_admin_manager', 'By HR Manager'),
                    ('hr_admin_officer', 'By HR Officer'),
                    ('hr_admin_admin', 'By HR Admin'),
                    ('hr_group', 'By HR Group')],
                    string='Approver Type', required=True)
    leave_type_id = fields.Many2one('hr.leave.type', string='Leave Type')
    group_id = fields.Many2one('hr.group', string='Group')


class HrLeaveResumer(models.Model):
    _name = 'hr.leave.resumer'
    _description = 'HR Leave Resumer'
    _order = 'sequence'

    sequence = fields.Integer('Sequence', required=True)
    approver_type = fields.Selection([
                    ('coach', 'By Coach'),
                    ('manager', 'By Manager'),
                    ('dept_manager', 'By Department Manager'),
                    ('hr_admin_manager', 'By HR Manager'),
                    ('hr_admin_officer', 'By HR Officer'),
                    ('hr_admin_admin', 'By HR Admin'),
                    ('hr_group', 'By HR Group')],
                    string='Approver Type', required=True)
    leave_type_id = fields.Many2one('hr.leave.type', string='Leave Type')
    group_id = fields.Many2one('hr.group', string='Group')


class HrLeaveApprovalHistory(models.Model):
    _name = 'hr.leave.approval.history'
    _description = 'HR Leave Approval History'
    _order = 'sequence'

    sequence = fields.Integer('Sequence', required=True)
    approver_type = fields.Selection([
                    ('coach', 'By Coach'),
                    ('manager', 'By Manager'),
                    ('dept_manager', 'By Department Manager'),
                    ('hr_admin_manager', 'By HR Manager'),
                    ('hr_admin_officer', 'By HR Officer'),
                    ('hr_admin_admin', 'By HR Admin'),
                    ('hr_group', 'By HR Group')],
                    string='Approver Type', required=True)
    is_approve = fields.Boolean('Is Approved?')
    approved_by_id = fields.Many2one('res.users', string='Approved By', readonly=True)
    approved_time = fields.Datetime('Approved Time', readonly=True)
    hr_leave_id = fields.Many2one('hr.leave', string='Leave')
    group_id = fields.Many2one('hr.group', string='Group')


class HrLeaveResumeHistory(models.Model):
    _name = 'hr.leave.resume.history'
    _description = 'HR Leave Resume History'
    _order = 'sequence'

    sequence = fields.Integer('Sequence', required=True)
    approver_type = fields.Selection([
                    ('coach', 'By Coach'),
                    ('manager', 'By Manager'),
                    ('dept_manager', 'By Department Manager'),
                    ('hr_admin_manager', 'By HR Manager'),
                    ('hr_admin_officer', 'By HR Officer'),
                    ('hr_admin_admin', 'By HR Admin'),
                    ('hr_group', 'By HR Group')],
                    string='Approver Type', required=True)
    is_approve = fields.Boolean('Is Approved?')
    approved_by_id = fields.Many2one('res.users', string='Approved By', readonly=True)
    approved_time = fields.Datetime('Approved Time', readonly=True)
    hr_leave_id = fields.Many2one('hr.leave', string='Leave')
    group_id = fields.Many2one('hr.group', string='Group')


class HrGroup(models.Model):
    _name = 'hr.group'
    _description = 'HR Group'

    name = fields.Char('Name', required=True)
    emp_approve_ids = fields.Many2many('hr.employee', string='Employees')


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    group_id = fields.Many2one('hr.group', string='Group', groups="hr.group_hr_user")


class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    group_id = fields.Many2one('hr.group', string='Group', readonly=True)


class AttendanceUploadLog(models.Model):
    _inherit = 'att.upload.log'

    leave_ids = fields.One2many("hr.leave", "att_log_id", string="Leaves")
    leave_count = fields.Integer("Total Uploaded Leaves", compute="_compute_leave_count")

    def _compute_leave_count(self):
        for rec in self:
            rec.leave_count = len(rec.leave_ids.ids)


class LeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    is_auto_generate = fields.Boolean('Is Auto Generate?')

    @api.onchange('employee_id')
    def onchange_contract(self):
        if self.employee_id:
            self.number_per_interval = self.employee_id.contract_id.leave_allocation

    def create_auto_type_leave_allocation(self):
        LeaveType = self.env['hr.leave.type']
        Employee = self.env['hr.employee']

        leave_types = LeaveType.search([
            ('is_auto_allocate', '=', True)
        ])
        if not leave_types:
            _logger.error(_('Auto Leave Allocation :: Leave Type is not configured.'))
            return

        employees = Employee.search([('contract_id.leave_allocation', '>', 0)])
        if not employees:
            _logger.error(_('Auto Leave Allocation :: Employee->Contract -> Allocation not defined.'))

        today = fields.Date.today()
        for leave_type in leave_types:
            if leave_type.auto_allocation_date and datetime.strptime(leave_type.auto_allocation_date.strftime('%m-%Y'), '%m-%Y') > datetime.strptime(
                    today.strftime('%m-%Y'), '%m-%Y'):
                continue
            for employee in employees:
                leave_allocation = employee.contract_id.leave_allocation
                if leave_allocation > 0.0:
                    self.create({
                        'name': leave_type.name + ' - ' + today.strftime('%B'),
                        'holiday_type': 'employee',
                        'employee_id': employee.id,
                        'holiday_status_id': leave_type.id,
                        'allocation_type': 'regular',
                        'number_of_days': leave_allocation,
                        'is_auto_generate': True,
                        'mode_company_id': employee.company_id.id,
                    })
                    _logger.info("Auto Leave Allocation : %s - Added %s on %s" % (employee.name, leave_allocation, leave_type.name))
            leave_type.write({'auto_allocation_date': today})
