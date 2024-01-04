# -*- coding: utf-8 -*-
from odoo.exceptions import UserError

from odoo import fields, models, api


class HrEncashWizard(models.TransientModel):
    _name = 'hr.encashment.wizard'
    _description = 'Hr Encashment Wizard'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    leave_type_id = fields.Many2one('hr.leave.type', string='Leave Type')
    approved_leave_count = fields.Float(string='Leaves eligible to Encash')
    no_of_leaves = fields.Float(string='Leaves to Encash')

    @api.onchange('leave_type_id')
    def _compute_approved_leave_count(self):
        if self.leave_type_id:
            leave = self.env['hr.leave.report'].search([('state', '=', 'validate'),
                                                        ('employee_id', '=', self.employee_id.id),
                                                        ('holiday_status_id', '=', self.leave_type_id.id)])
            self.approved_leave_count = sum(leave.mapped('number_of_days'))

    def create_allocated_leave(self, leave_type, no_of_leave):
        leave_allocation = self.env['hr.leave.allocation']
        encash = leave_allocation.create({
            'employee_id': self.employee_id.id,
            'holiday_status_id': leave_type,
            'number_of_days': no_of_leave,
            'state': 'encashed'
        })

    def action_post(self):
        for rec in self:
            leave_allocation = self.env['hr.leave.allocation']
            allocations = leave_allocation.search([
                ('employee_id', '=', rec.employee_id.id),
                ('holiday_status_id', '=', rec.leave_type_id.id),
                ('state', '=', 'validate')
            ])
            if not allocations:
                raise UserError('No leave allocations found.')

            if rec.no_of_leaves <= 0:
                raise UserError('Leaves to encashment must be greater than zero.')
            encash_history = self.env['hr.encashment.history'].create({
                'employee_id': rec.employee_id.id,
                'leave_type_id': rec.leave_type_id.id,
                'no_of_days': rec.no_of_leaves,
                'date': fields.Date.today(),
                'encashment_amount': self.employee_id.contract_id.wage*rec.no_of_leaves/26
            })
            no_of_days = rec.no_of_leaves
            while no_of_days > 0:
                for allocation in allocations:
                    try:
                        if allocation.number_of_days == no_of_days:
                            allocation.state_change_to_encash()
                            return
                        elif allocation.number_of_days < no_of_days:
                            allocation.state_change_to_encash()
                            no_of_days -= allocation.number_of_days
                        elif allocation.number_of_days > no_of_days:
                            allocation.number_of_days -= no_of_days
                            self.create_allocated_leave(rec.leave_type_id.id, no_of_days)
                            return
                    except:
                        return


