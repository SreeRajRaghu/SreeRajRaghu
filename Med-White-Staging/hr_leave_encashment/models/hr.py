# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models, _
_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def action_employee_encashment(self, employee):
        return {
            'name': _('Employee Encashment'),
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('hr_leave_encashment.view_hr_encashment_wizard').id,
            'res_model': 'hr.encashment.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {
                'default_employee_id': employee.id
            }
        }


class LeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    state = fields.Selection(selection_add=[
        ('encashed', 'Encashed')])

    def state_change_to_encash(self):
        for rec in self:
            rec.state = 'encashed'


class InheritLeaveSummary(models.Model):
    _inherit = "hr.leave.report"

    state = fields.Selection(selection_add=[
        ('encashed', 'Encashed')])
