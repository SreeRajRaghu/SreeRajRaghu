# -*- coding: utf-8 -*-

from datetime import datetime, time, timedelta
from pytz import timezone, UTC
import time

from odoo import fields, models, _
from odoo.exceptions import UserError


class ResumeWorkWizard(models.TransientModel):
    _name = 'resume.work.wizard'
    _description = 'Resume Wizard'

    date_resume = fields.Datetime('Resume Date', required=True, default=lambda *a: time.strftime('%Y-%m-%d 00:00:00'))

    def action_resume(self):
        self.ensure_one()
        HRLeave = self.env['hr.leave']
        HRLeaveAllocation = self.env['hr.leave.allocation'].sudo()
        Employee = self.env['hr.employee']

        active_id = self.env.context.get('active_id')
        if active_id:
            tz = self.env.user.tz if self.env.user.tz else 'UTC'
            leave = self.env['hr.leave'].sudo().browse(active_id)
            if self.date_resume < leave.date_from:
                raise UserError(_("Resume Date could be earlier than Leave From Date"))

            remain_approvals = leave.leave_resume_history_ids.filtered(lambda x: not x.is_approve)
            if remain_approvals:
                if len(remain_approvals) == 1:
                    current_remain_approval = remain_approvals
                    current_remain_approval.write({
                        'approved_by_id': self.env.uid,
                        'approved_time': fields.Datetime.now(),
                        'is_approve': True,
                    })
                else:
                    current_user_employee = Employee.search([('user_id', '=', self.env.user.id)], limit=1)
                    if current_user_employee == leave.employee_id:
                        leave.write({'is_employee_resume': True})
                        return True

                    current_remain_approval = remain_approvals[0]
                    current_remain_approval.write({
                        'approved_by_id': self.env.uid,
                        'approved_time': fields.Datetime.now(),
                        'is_approve': True,
                    })
                    return True

            if self.date_resume:
                resume_time = self.date_resume.time()
                resume_date = timezone(tz).localize(datetime.combine(self.date_resume, resume_time)).astimezone(UTC).replace(tzinfo=None)
                if resume_date > leave.date_to:
                    days = leave._get_number_of_days(leave.date_to, resume_date, leave.employee_id.id)['days']
                else:
                    days = leave._get_number_leave_days(resume_date, leave.date_to, leave.employee_id.id)['days'] * -1
            created_allocation = False
            created_leave = False
            if days < 0.0:
                created_allocation = HRLeaveAllocation.create({
                    'name': 'Due to Early Resume',
                    'employee_id': leave.employee_id.id,
                    'number_of_days': abs(days),
                    'holiday_type': 'employee',
                    'holiday_status_id': leave.holiday_status_id.id,
                    'state': 'validate',
                }).id
            else:
                created_leave = HRLeave.create({
                    'employee_id': leave.employee_id.id,
                    'holiday_status_id': leave.holiday_status_id.id,
                    'date_from': leave.date_to + timedelta(days=1),
                    'date_to': self.date_resume,
                    'request_date_from': leave.date_to.strftime('%Y-%m-%d'),
                    'request_date_to': self.date_resume.strftime('%Y-%m-%d'),
                    'state': 'validate',
                }).id
            leave.write({
                'date_resume': self.date_resume,
                'resume_days': days,
                'allocation_request_id': created_allocation,
                'leave_request_id': created_leave,
                'is_resume': True,
            })
        return True
